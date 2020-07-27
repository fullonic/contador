"""Endesa e-distribution consume info scrapper."""

import datetime
import json
import os
import time
from collections import defaultdict
from typing import Dict, List, Tuple
import logging

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


def _wait_to_be_clickable(driver, selector):
    """Deal with object present on DOM but not be clickable because spinning gif."""
    reties = 0
    while reties < 5:
        try:
            btn = driver.find_element_by_css_selector(selector)
            btn.click()
            break
        except ElementClickInterceptedException:
            time.sleep(0.5)
            reties += 1
    return


def _read_succeed(driver):
    """Ensure that "consulta contador" succeed."""
    status = False
    try:
        driver.find_element_by_css_selector(".percent")
        status = True  # Succeed
    except NoSuchElementException:
        # means that error is consumption value is yet not visible
        # checks if there is a error
        try:
            # Checks if there was a error
            error = driver.find_element_by_css_selector("[title='ENTENDIDO']")
            error.click()
            info_log.error("Solicitud fallada [Error Popup]")
        except NoSuchElementException:
            # Probably is still present the spinner gif we run it again
            info_log.info("Todavía procesando")
    return status


#########################
# JSON Files
#########################
def get_config():
    """Load script configuration file."""
    with open("config.json") as f:
        return json.load(f)


def storage(type_) -> dict:
    """Get users from json file."""
    db = {"users": "users.json", "results": "results.json"}
    with open(db[type_], "r") as f:
        data = json.load(f)
    return data


def save(data):
    results: dict = storage("results")
    updated = defaultdict(list)
    updated.update(results)
    for k, v in data.items():
        updated[k].append(v)
    with open("results.json", "w") as f:
        json.dump(updated, f)


#########################
# Data collector
#########################


def browser_setup():
    """Set a driver object."""
    cfg = get_config()["browser"]
    profile = FirefoxProfile()
    user_agent = UserAgent()
    profile.native_events_enabled = cfg["native_events_enabled"]
    profile.set_preference("general.useragent.override", user_agent.random)
    opts = FirefoxOptions()
    opts.headless = cfg["headless"]
    driver = Firefox(options=opts)
    driver.implicitly_wait(cfg["timeout"])
    return driver


def login(driver, user=None, password=None):
    """Deal with user login."""
    info_log.info("Inserindo los datos")
    if not all([user, password]):
        user = input("Usuario: ")
        password = input("Contraseña: ")
    user_in = driver.find_element_by_name("username")
    user_in.send_keys(user)
    password_in = driver.find_element_by_name("password")
    password_in.send_keys(password)
    submit = driver.find_element_by_css_selector(".slds-button_brand")
    submit.click()
    info_log.info("Usuari@ logged")


def contador_online(driver):
    """Navigate into consume area."""
    btn = driver.find_element_by_css_selector(
        "div.slds-col:nth-child(8) > div:nth-child(1) > div:nth-child(1)"
    )
    btn.click()
    info_log.info("Area Contador Online")
    driver.find_element_by_name("ActionReconectar").click()


def get_actual_consume(
    username: str, page: str, driver: webdriver
) -> Tuple[bool, Dict[str, tuple]]:
    """Extract values from page source after getting readings values."""
    dt = datetime.datetime.now()
    try:
        soup = bs4.BeautifulSoup(page, features="html.parser")
        actual_read = _actual_read(soup.select(".description")[0].text)
        percent = _relative_percent(soup.select(".percent")[0].text)
        max_power = _max_power(soup.select(".max > span:nth-child(1)")[0].text)
        return (
            True,
            {
                username: (
                    dt.strftime("%d-%m-%Y_%H:%M:%S"),
                    actual_read,
                    percent,
                    max_power,
                )
            },
        )
    except IndexError:
        # It means that was not possible to get information from page
        # TODO: reschedule task
        return (
            False,
            {username: (False, "Failed to get data", dt.strftime("%d-%m-%Y_%H:%M:%S"))},
        )


def lectura(driver, retry=True):
    """Request the actual reading to the service.

    If it fails, it will automatically retry one try.
    TODO: Add a reschedule if it fails twice
    """
    info_log.info("Solicitando los valores de lectura ...")
    _wait_to_be_clickable(driver, "[title='Consultar Contador']")
    spinner = driver.find_element_by_class_name("slds-spinner_container")
    while spinner.is_displayed():
        time.sleep(1)
        if _read_succeed(driver):
            info_log.info("Solicitud de aceptada")
            status = True
            break
        else:
            info_log.error("Solicitud fallada")
            if retry:
                info_log.info("Reintentando ...")
                lectura(driver, False)
            status = False
            break
    return status


def _get_reading(user: dict):
    start = time.perf_counter()
    username = user["username"]
    password = user["password"]
    # Browser setup
    driver = browser_setup()
    driver.get("https://www.edistribucion.com/es/index.html")
    _wait_to_be_clickable(driver, "li.toggleonopen:nth-child(4)")

    # log in form
    login(driver, username, password)
    contador_online(driver)
    lectura(driver)
    succeed, values = get_actual_consume(username, driver.page_source, driver)
    driver.close()
    print("#" * 20)
    return succeed, values


def save_results(succeed, data):
    if succeed:
        save(data)

    else:
        # TODO: Add retry again
        pass
        # failed.append(data)


def read():
    """Single thread script entrypoint."""
    users = storage("users")
    for user in users["usuarios"]:
        succeed, values = _get_reading(user)
        save_results(succeed, values)


def read_multiple(pool):
    """Threadpool script entrypoint."""
    users = storage("users")["usuarios"]
    results = pool.map(_get_reading, users)
    for res in results:
        succeed, values = res
        save_results(succeed, values)


if __name__ == "__main__":
    read()  # for testing
