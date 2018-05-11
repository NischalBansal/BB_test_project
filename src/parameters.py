#home_path = "/home/pscan/"
home_path = "/opt/pscan/"
log_path = "/var/pscan/"
system_config_filename = "system_config.txt"
scan_record_filename = "scan_record.txt"
subscriber_filename = "subscriber.txt"
uuid = "00001101-0000-1000-8000-00805F9B34FB"
mail_interval = 1
fileName = "Record-%d-%m-%Y-%H-%M-%S.txt"
server_ip = '10.131.10.191'
server_port = 5011
mail_to_addr = ""
mail_server_ip = "10.131.253.244"


datahub_path = log_path
url = "http://52.37.106.39/api/device"
headers = {'Content-type': 'application/json'}
#testdata = {"Deviceid":"IOTD5 - L500","ConnectedCount":1770,"userId":1}
filelistFile_path = datahub_path + "statusfile/newfiles.txt"
filestoScan_path = datahub_path + "filestoSend/"
filescannedDIR_path = datahub_path + "filesSent/"
filescannedFIle_path = datahub_path + "statusfile/sentfile.txt"
wifi_ssid = 'IoT'
wifi_password = 'IoT@Rsys'
