import yaml
import time
import json
import requests
import csv

from datetime import datetime, timedelta
from prtg.sensor.result import CustomSensorResult
from prtg.sensor.units import ValueUnit


def post(host, url, data, verify=False, disable_warning=True):
    """Request implementation, to simplify error handling.

    Args:
        host (string): Hostname of Logger
        url (string): URL for the API Endpoint
        data (array): Payload of the body
        verify (bool, optional): SSL Verification
        disable_warning (bool, optional): Disable SSL warnings

    Returns:
        json: An array upon success, or empty if HTTP 204.
        If an error is caught the error will be printed
        and the application will exit.

    """
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    if disable_warning:
        requests.packages.urllib3.disable_warnings()
    try:
        response = requests.post(
            'https://' + host + url, json=data, headers=headers, verify=verify)
        response.raise_for_status()
        if response.status_code == 200:
            if response.text:
                response = json.loads(response.text)
        else:
            response = response.text
    except requests.exceptions.HTTPError as err:
        print(response.text)
        print(err)
        return (err)
    return response


def login(host, username, password):
    """Authenticate with the ArcSight Logger.

    Args:
        host (string): Hostname of Logger
        username (string): Username to authenticate with
        password (string): Password related to the user account

    Returns:
        json: On successful login it will return the related authtoken

    """
    url = '/core-service/rest/LoginService/login'
    payload = {
        "log.login": {
            "log.login": username,
            "log.password": password
        }
    }
    response = post(host, url, data=payload)
    return response


def logout(host, authtoken):
    """Close the provided authtoken.

    Args:
        host (string): Hostname of Logger
        authtoken (string): Token for the current session

    Returns:
        Null: Returns an empty HTTP 204 upon success

    """
    url = '/core-service/rest/LoginService/logout'
    payload = {
        "log.logout": {
            "log.authToken": authtoken,
        }
    }
    response = post(host, url, data=payload)
    return response


def search(host, authtoken, query, search_id, **kwargs):
    """Start a background search job.

    Args:
        host (string): Hostname of Logger
        authtoken (string): Token for the current session
        query (string): Which query to run
        search_id (int): The search_id to be generated for the search
        **kwargs: All arguments marked as optional in documentation

    Returns:
        json: If successful returns a sessionId, this ID is only
        related if you want to find the running search
        on the ArcSight Logger web interface. This is not related
        to the search_id provided by the user.

    """
    url = '/server/search'
    payload = {
        'search_session_id': search_id,
        'user_session_id': authtoken,
        'query': query,
        **kwargs
    }
    response = post(host, url, data=payload)
    return response


def status(host, authtoken, search_id):
    """Retrieve status of an existing search.

    Args:
        host (string): Hostname of Logger
        authtoken (string): Token for the current session
        search_id (int): The search_id for the search to take action on

    Returns:
        json: An array showing the current status of a search

    """
    url = '/server/search/status'
    payload = {
        'search_session_id': search_id,
        'user_session_id': authtoken,
    }
    response = post(host, url, data=payload)
    return response


def wait(host, authtoken, search_id):
    """Wait until a search is finalized, checking every 5 seconds.

    Args:
        host (string): Hostname of Logger
        authtoken (string): Token for the current session
        search_id (int): The search_id for the search to take action on

    Returns:
        json: An array showing the current status of a search

    """
    response = status(host, authtoken, search_id)
    while response['status'] != 'complete':
        response = status(host, authtoken, search_id)
        if response['status'] != 'complete':
            time.sleep(5.0)
    return response


def events(host, authtoken, search_id, **kwargs):
    """Retrieve events related to a running or finalized search.

    Args:
        host (string): Hostname of Logger
        authtoken (string): Token for the current session
        search_id (int): The search_id for the search to take action on
        **kwargs: All arguments marked as optional in documentation

    Returns:
        json: Array including the events for the related search_id

    """
    url = '/server/search/events'
    payload = {
        'search_session_id': search_id,
        'user_session_id': authtoken,
        **kwargs
    }
    response = post(host, url, data=payload)
    return response


def raw_events(host, authtoken, search_id, row_ids):
    """Retrieve the raw CEF formatted events from search_id.

    Args:
        host (string): Hostname of Logger
        authtoken (string): Token for the current session
        search_id (int): The search_id for the search to take action on
        row_ids (array): An array of IDs which raw events should be retrieved from

    Returns:
        json: An array of CEF formatted raw events related to the row_ids

    """
    url = '/server/search/raw_events'
    payload = {
        'search_session_id': search_id,
        'user_session_id': authtoken,
        'row_ids': [row_ids]
    }
    response = post(host, url, data=payload)
    return response


def histogram(host, authtoken, search_id):
    """Retrieve data from a related search_id in a histogram format.

    Args:
        host (string): Hostname of Logger
        authtoken (string): Token for the current session
        search_id (int): The search_id for the search to take action on

    Returns:
        json: An array with bucket counts, width
        and the relevant count for each bucket

    """
    url = '/server/search/histogram'
    payload = {
        'search_session_id': search_id,
        'user_session_id': authtoken,
    }
    response = post(host, url, data=payload)
    return response


def drilldown(host, authtoken, search_id, start_time, end_time):
    """Drill down a finalized search, to retrieve events from a smaller time.

    Args:
        host (string): Hostname of Logger
        authtoken (string): Token for the current session
        search_id (int): The search_id for the search to take action on
        start_time (string): The starttime for the drilldown
        end_time (string): The endtime for the drilldown

    Returns:
        Null: Returns an empty HTTP 204 response upon success

    """
    url = '/server/search/drilldown'
    payload = {
        'search_session_id': search_id,
        'user_session_id': authtoken,
        'start_time': start_time,
        'end_time': end_time,
    }
    response = post(host, url, data=payload)
    return response


def chart_data(host, authtoken, search_id, **kwargs):
    """Return results to be used in charts or statistics.

    Args:
        host (string): Hostname of Logger
        authtoken (string): Token for the current session
        search_id (int): The search_id for the search to take action on
        **kwargs: All arguments marked as optional in documentation

    Returns:
        json: An array of aggregated data based on the specific search_id

    """
    url = '/server/search/chart_data'
    payload = {
        'search_session_id': search_id,
        'user_session_id': authtoken,
        **kwargs
    }
    response = post(host, url, data=payload)
    return response


def stop(host, authtoken, search_id):
    """Halts an ongoing search while keeping the currently found results.

    Args:
        host (string): Hostname of Logger
        authtoken (string): Token for the current session
        search_id (int): The search_id for the search to take action on

    Returns:
        null: An empty HTTP 204 response upon success

    """
    url = '/server/search/stop'
    payload = {
        'search_session_id': search_id,
        'user_session_id': authtoken,
    }
    response = post(host, url, data=payload)
    return response


def close(host, authtoken, search_id):
    """Close down an ongoing or finished search, and delete it's current results.

    Args:
        host (string): Hostname of Logger
        authtoken (string): Token for the current session
        search_id (int): The search_id for the search to take action on

    Returns:
        null: An empty HTTP 204 response upon success

    """
    url = '/server/search/close'
    payload = {
        'search_session_id': search_id,
        'user_session_id': authtoken,
    }
    response = post(host, url, data=payload)
    return response


def create_logger_search(_username, _password, _address):
    username = _username
    password = _password
    address = _address
    token = login(address, username, password)
    logger = dict()
    #   3.2 - Populate logger object with these ınfoırmatioın adn flag the API Connectivity to true
    if "log.loginResponse" in str(token):
        logger['api_connectivity'] = True
        login_token = (token['log.loginResponse'])['log.return']
        logger['token'] = login_token
    else:
        logger['api_connectivity'] = False
        # print("Logger Baglanma Hatası : " + str(token))
        exit(1)
    #
    #  4 - Create Search
    #
    # 4.1 -  Zaman aralıgı olustur
    currentTime = datetime.now() - timedelta(minutes=10)
    startTime = currentTime.strftime("%Y-%m-%dT%H:%M:%S.000+03:00")
    endTime = time.strftime("%Y-%m-%dT%H:%M:%S.000+03:00")
    # 4.2  - Submit Search
    query = '|top 6000 deviceVendor deviceProduct deviceHostName deviceAddress | sort deviceVendor deviceProduct deviceAddress deviceHostName'
    search_id = int(round(time.time() * 1000))
    search_response = search(address, login_token, query, search_id, start_time=startTime, end_time=endTime,
                             local_search=False)
    session_id = search_response['sessionId']
    time.sleep(0.15)
    status_response = dict()
    combined_result_list = list()
    while True:
        status_response = status(address, login_token, search_id)
        search_status = status_response['status']
        # print(response)
        if search_status == 'complete':
            break
        if search_status == 'error':
            exit(1)
        time.sleep(5)
    # 4.4 Bütün aramalarımız başarılı tamamlandıktan sonra result'ları çekeriz.Her seferinfde 25 adet result çekebiliyoruz.
    hit_count = status_response['hit']
    offset = 0
    lenght = 25  # max 100

    while offset < hit_count:
        tmp = chart_data(address, login_token, search_id, offset=offset, lenght=lenght)
        offset = offset + lenght
        for r in tmp['results']:
            combined_result_list.append(r)

    #result'ları birleştir

    # close and logout
    close(address, login_token, search_id)
    logout(address, login_token)
    return combined_result_list


def calculate_total_event_count(results):
    total_count = 0
    for result in results:
        i = int(result[4])
        total_count = total_count + i
    return total_count


def test_device(device_from_list, normalized_devices_from_result):
    """
    :rtype: bool
    """
    # TEST deviceInResults
    for device_from_result in normalized_devices_from_result:
        if device_from_list == device_from_result:
            return True
        else:
            continue

    return False


def get_device_event_count(normalized_device, normalized_results_with_count):
    for device_from_result in normalized_results_with_count:
        dummy = (str(device_from_result).split(','))
        count = dummy[4]
        result = f"{dummy[0]},{dummy[1]},{dummy[2]},{dummy[3]}"
        if str(result) == normalized_device:
            return count
        else:
            continue
    return 0


def normalize_result(results):
    normalized_strings = list()
    normalized_strings_with_count = list()
    for result in results:
        deviceVendor = str(result[0]).lower().strip()
        deviceProduct = str(result[1]).lower().strip()
        deviceHostName = str(result[2]).lower().strip()
        deviceAddress = str(result[3]).lower().strip()
        count = str(result[4]).lower().strip()
        normalized_strings.append("{0},{1},{2},{3}".format(deviceVendor, deviceProduct, deviceHostName, deviceAddress))
        normalized_strings_with_count.append(
            "{0},{1},{2},{3},{4}".format(deviceVendor, deviceProduct, deviceHostName, deviceAddress, count))
    dict_nm_results = dict()
    dict_nm_results['normalized_results'] = normalized_strings
    dict_nm_results['normalized_results_with_count'] = normalized_strings_with_count
    return dict_nm_results


def normalize_result_with_count(results):
    normalized_strings = list()
    for result in results:
        deviceVendor = str(result[0]).lower().strip()
        deviceProduct = str(result[1]).lower().strip()
        deviceHostName = str(result[2]).lower().strip()
        deviceAddress = str(result[3]).lower().strip()
        count = str(result[4]).lower().strip()
        normalized_result_string = deviceVendor + "," + deviceProduct + "," + deviceHostName + "," + deviceAddress + "," + count
        normalized_strings.append(normalized_result_string)
    return normalized_strings


def normalize_devices(devices):
    normalized_strings = list()
    for device in devices:
        # " işaretlerini sil
        device = device.replace('"', '')
        # küçük harfe çevir ve trimle
        device = device.strip().lower()
        if device != '':
            normalized_strings.append(device)
        else:
            continue
    return normalized_strings


def check_ping(str_hostname):
    hostname = str_hostname
    # For Windows
    import os
    response = os.system("ping -n 1 " + hostname)
    # For Linux
    # response = os.system("ping -c 1 " + hostname)
    # and then check the response...
    if response == 0:
        pingstatus = "Network Active"
    else:
        pingstatus = "Network Error"

    return pingstatus


def remove_count_from_devices(normalized_devices_from_list_with_count):
    device_tag = list()

    for device in normalized_devices_from_list_with_count:
        tmp = device.split(',')
        tmp_device = "{0},{1},{2},{3}".format(tmp[0], tmp[1], tmp[2], tmp[3])
        device_tag.append(tmp_device)
    return device_tag


# MAIN
devices = """"Fortinet","Fortigate","OBT-DcFw3","","792425"
"Palo Alto Networks","PAN-OS","DC-INT-FW2","","637923"
"Fortinet","Fortigate","OBT-DR-DcFw","","374771"
"Palo Alto Networks","PAN-OS","DRC-INT-FW1","","163081"
"Fortinet","Fortigate","OBT-DR-DcFw","10.224.147.1","39327"
"Microsoft","Microsoft Windows","OBTVM-DC2.odeabank.com.tr","10.224.3.17","15726"
"Forcepoint","Security","","10.224.105.41","12811"
"Microsoft","Microsoft Windows","OBT-DC1.odeabank.com.tr","10.224.3.16","12276"
"Forcepoint","Security","","10.224.105.43","12132"
"Fortinet","FortiGate-300C","FG300C3913600183","","10885"
"Fortinet","Fortigate","FG300C3913600183","","10500"
"F5","ASM","OBT-F5-Int3.odeabank.com.tr","10.224.5.51","10446"
"Forcepoint","Security","","10.224.105.42","7906"
"Microsoft","Microsoft Windows","OBTVM-DC1.odeabank.com.tr","10.224.3.71","7511"
"Unix","auditd","exa1dbadm01","","5676"
"F5","ASM","OBT-F5-Ext1.odeabank.com.tr","10.224.12.202","5647"
"Fortinet","FortiGate-1000C","OLIVE-ODB-FW1","","1980"
"Fortinet","FortiWiFi-60CX-ADSL-A","NETSEC-60CX-FW","","1519"
"Pulse Secure","Pulse Connect Secure","OBT-Pulse1","","988"
"Fortinet","Fortigate","FW-3P-HA1","","903"
"Fortinet","FortiGate-300C","FW-3P-HA1","","840"
"ArcSight","Logger","","127.0.0.1","225"
"Forcepoint","Email Security","v10k1-esg","10.224.17.15","188"
"Forcepoint","Email Security","v10k2-esg","10.224.17.16","171"
"ArcSight","Logger","","10.224.104.21","85"
"Palo Alto Networks","PAN-OS","Panorama","","51"
"Fortinet","FortiGate-300C","FW-3P-HA2","","11"
"""

logger_username = 'admin'
logger_password = 'R00t123!'
logger_address = '192.168.160.129'

# DO NOT EDIT BELOW THIS LINE

lst_devices = devices.split('\n')
normalized_devices_from_list_with_count = normalize_devices(lst_devices)
normalized_devices_from_list_without_count = remove_count_from_devices(normalized_devices_from_list_with_count)
# Create Search at logger

raw_results = create_logger_search(logger_username, logger_password, logger_address)
results=raw_results
# Gelen log sayılarını topla ve toplam event sayısını bul
total_log_count = calculate_total_event_count(results)

# Normalization of the results
dict_nm_results = normalize_result(results)
normalized_results = dict_nm_results['normalized_results']
normalized_results_with_count = dict_nm_results['normalized_results_with_count']

# Cihaz kayıtlarını result setinin içinde olup olmadığını test et
# testin doğru yanlış durumuna göre sorunlu ve sorunsuz cihazları ayır
no_log_devices = list()
log_devices = list()
for device in normalized_devices_from_list_without_count:
    if test_device(device, normalized_results):
        log_devices.append(device)
    else:
        no_log_devices.append(device)
# sorunsuz cihazların log count'ını al
# bunu ayrı bir liste içersinde tut
normalized_devices_with_count = list()
for device in log_devices:
    event_count = get_device_event_count(device, normalized_results_with_count)
    normalized_devices_with_count.append(str(device) + ',' + str(event_count))

# Sorunlu cihazların sonuna count olarak 0 ekle
no_log_devices_with_count = list()

for device in no_log_devices:
    device_str = f"{device},0"
    no_log_devices_with_count.append(device_str)

########################
# PRTG OUTPUT OLUŞTUR
if __name__ == "__main__":
    csr = CustomSensorResult(text="This sensor contains ArcSight Logger device results")
    csr.add_primary_channel(name="TOTAL EVENT COUNT",
                            value=int(total_log_count),
                            unit=ValueUnit.COUNT
                            )
    for device in normalized_devices_with_count:
        lst = str(device).split(',')
        tag = f"DeviceVendor = {lst[0]},DeviceProduct :{lst[1]},DeviceHostName : {lst[2]},DeviceAddress : {lst[3]}"
        count = int(lst[4])
        csr.add_channel(name=tag,
                        value=count,
                        unit=ValueUnit.COUNT)
    for device in no_log_devices_with_count:
        lst = str(device).split(',')
        tag = f"DeviceVendor = {lst[0]},DeviceProduct :{lst[1]},DeviceHostName : {lst[2]},DeviceAddress : {lst[3]}"
        count = int(lst[4])
        csr.add_channel(name=tag,
                        value=count,
                        unit=ValueUnit.COUNT)
    print(csr.json_result)
#    except Exception as e:
#        csr = CustomSensorResult(text="Python Script execution error")
#        csr.error = "Python Script execution error: %s" % str(e)
#        print(csr.json_result)
