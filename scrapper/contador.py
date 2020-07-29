"""Endesa e-distribution consume info scrapper."""

import datetime
import json
import os
import time
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple
import logging
from dataclasses import dataclass
import bs4  # type: ignore
from fake_useragent import UserAgent  # type: ignore
from selenium import webdriver  # type: ignore
from selenium.common.exceptions import (  # type: ignore
    ElementClickInterceptedException,
    NoSuchElementException,
)
from selenium.webdriver import FirefoxOptions  # type: ignore
from selenium.webdriver import Firefox, FirefoxProfile

HEADLESS = False
TIMEOUT = 15
base_path = Path(__file__).parent

#########################
# loggers
#########################
def info_logger():
    """Info logging."""
    info_log = logging.getLogger(__name__)
    info_log.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    logger_formatter = logging.Formatter("[%(levelname)s] - %(message)s")
    handler.setFormatter(logger_formatter)
    info_log.addHandler(handler)
    return info_log


info_log = info_logger()


#########################
# Helper functions
#########################
def _to_float(value: str) -> float:
    """Convert stringified float number to a python float."""
    return float(value.replace(",", "."))


def _actual_read(read_: str) -> float:
    """Clean power consume value.

    'Potencia Instantánea Actual1,22 kW' -> 1.22
    """
    read_ = read_.strip("Potencia Instantánea Actual").strip(" kW")
    return _to_float(read_)


def _relative_percent(percent: str) -> float:
    percent = percent.strip("%")
    return _to_float(percent)


def _max_power(power: str) -> float:
    power = power.strip(" kW")
    return _to_float(power)


#########################
# JSON Files
#########################
def get_config():
    """Load script configuration file."""
    with open(f"{base_path}/config.json") as f:
        return json.load(f)


def storage(type_) -> dict:
    """Get users from json file."""
    db = {"users": "users.json", "results": "results.json"}
    with open(f"{base_path}/{db[type_]}", "r") as f:
        data = json.load(f)
    return data


def browser_setup():
    """Set a driver object."""
    cfg = get_config()["browser"]
    profile = FirefoxProfile()
    user_agent = UserAgent()
    profile.native_events_enabled = cfg["native_events_enabled"]
    profile.set_preference("general.useragent.override", user_agent.random)
    opts = FirefoxOptions()
    opts.headless = cfg["headless"]
    driver = Firefox(options=opts, executable_path=cfg["gecko_driver"])
    driver.implicitly_wait(cfg["timeout"])
    return driver


def save_results(results):
    """Save data after reading cycle."""
    data: dict = storage("results")
    updated = defaultdict(list)
    updated.update(data)
    for res in results:
        succeed, values = res
        if succeed:
            for k, v in values.items():
                updated[k].append(v)
        else:
            # TODO: Add trace of failed readings
            # failed.append(data)
            pass
    with open(f"{base_path}/results.json", "w") as f:
        json.dump(updated, f)


#########################
# Data collector
#########################
@dataclass
class ReadConsumption:
    """Request power consumption for each user."""

    username: str = None
    password: str = None
    driver: webdriver = None

    def login(self):
        """Deal with user login."""
        info_log.info(f"[{self.username}] Inserindo los datos")
        if not all([self.username, self.password]):
            self.username = input("Usuario: ")
            self.password = input("Contraseña: ")
        user_in = self.driver.find_element_by_name("username")
        user_in.send_keys(self.username)
        password_in = self.driver.find_element_by_name("password")
        password_in.send_keys(self.password)
        submit = self.driver.find_element_by_css_selector(".slds-button_brand")
        submit.click()
        info_log.info(f"[{self.username}] Usuari@ logged")

    def contador_online(self):
        """Navigate into consume area."""
        btn = self.driver.find_element_by_css_selector(
            "div.slds-col:nth-child(8) > div:nth-child(1) > div:nth-child(1)"
        )
        btn.click()
        info_log.info(f"[{self.username}] Area Contador Online")
        self.driver.find_element_by_name("ActionReconectar").click()

    def get_actual_consume(self, page: str) -> Tuple[bool, Dict[str, tuple]]:
        """Extract values from page source after getting readings values."""
        dt = datetime.datetime.now()
        date = dt.strftime("%d-%m-%Y_%H:%M:%S")
        try:
            soup = bs4.BeautifulSoup(page, features="html.parser")
            actual_read = _actual_read(soup.select(".description")[0].text)
            percent = _relative_percent(soup.select(".percent")[0].text)
            max_power = _max_power(soup.select(".max > span:nth-child(1)")[0].text)
            return (
                True,
                {self.username: (date, actual_read, percent, max_power)},
            )
        except IndexError:
            # It means that was not possible to get information from page
            # TODO: reschedule task
            return (
                False,
                {self.username: (date, None, None, None)},
            )

    def wait_to_be_clickable(self, selector):
        """Deal with object present on DOM but not be clickable because spinning gif."""
        reties = 0
        while reties < 5:
            try:
                btn = self.driver.find_element_by_css_selector(selector)
                btn.click()
                break
            except ElementClickInterceptedException:
                time.sleep(0.5)
                reties += 1
        return

    def _read_succeed(self):
        """Ensure that "consulta contador" succeed."""
        status = False
        try:
            self.driver.find_element_by_css_selector(".percent")
            status = True  # Succeed
        except NoSuchElementException:
            # means that error is consumption value is yet not visible
            # checks if there is a error
            try:
                # Checks if there was a error
                error = self.driver.find_element_by_css_selector("[title='ENTENDIDO']")
                error.click()
                info_log.error(f"[{self.username}] Solicitud fallada [Error Popup]")
            except NoSuchElementException:
                # Probably is still present the spinner gif we run it again
                info_log.info(f"[{self.username}] Todavía procesando")
        return status

    def lectura(self, retry=True):
        """Request the actual reading to the service.

        If it fails, it will automatically retry one try.
        TODO: Add a reschedule if it fails twice
        """
        info_log.info(f"[{self.username}] Solicitando los valores de lectura ...")
        self.wait_to_be_clickable("[title='Consultar Contador']")
        spinner = self.driver.find_element_by_class_name("slds-spinner_container")
        while spinner.is_displayed():
            time.sleep(1)
            if self._read_succeed():
                info_log.info(f"[{self.username}] Solicitud de aceptada")
                status = True
                break
            else:
                info_log.error(f"[{self.username}] Solicitud fallada")
                if retry:
                    info_log.info(f"[{self.username}] Reintentando ...")
                    self.lectura(False)
                status = False
                break
        return status

    def get_reading(self):
        """Start reading."""
        self.driver.get("https://www.edistribucion.com/es/index.html")
        self.wait_to_be_clickable("li.toggleonopen:nth-child(4)")

        # log in form
        self.login()
        self.contador_online()
        self.lectura()
        succeed, values = self.get_actual_consume(self.driver.page_source)
        self.driver.close()
        return succeed, values


def read():
    """Single thread script entrypoint."""
    users = storage("users")["usuarios"]
    save_results(
        [
            ReadConsumption(
                username=user["username"],
                password=user["password"],
                driver=browser_setup(),
            ).get_reading()
            for user in users
        ]
    )
    print("#" * 20)


def _multiple(user):
    return ReadConsumption(
        username=user["username"], password=user["password"], driver=browser_setup(),
    ).get_reading()


def read_multiple(pool):
    """Threadpool script entrypoint."""
    users = storage("users")["usuarios"]
    results = pool.map(_multiple, users)
    save_results(results)
    print("#" * 20)


if __name__ == "__main__":
    read()  # for testing
