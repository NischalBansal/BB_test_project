"""
1. Takes input from user to setup IoT device
2. Scan for bluetooth devices in range
3. Transmit the information to subscriber
4. Delete the devices from scan list
"""
import datetime
import time
import pexpect
import subprocess
import sys
import json
import bluetooth
import os

class BluetoothctlError(Exception):
    """This exception is raised, when bluetoothctl fails to start."""
    pass


class Bluetoothctl:
    """A wrapper for bluetoothctl utility."""
    global devices_dict, message_record, system_config
    global device_id #, latitude, longitude
    global scan_interval
    global transmission_flag, debug_flag
    global path

    def __init__(self):
        out = subprocess.check_output("rfkill unblock bluetooth", shell = True)
        self.child = pexpect.spawn("bluetoothctl", echo = False)
        self.devices_dict = {}
        self.message_record = {}
        self.system_config = {}
        self.device_id = 1
        #self.latitude = 28.6093616
        #self.longitude = 77.3630105
        self.scan_interval = 10
        self.transmission_flag = "Y"
        self.debug_flag = "N"
        #self.path = os.getcwd()+"/"
        self.path = "/home/edison/"


    def save_config(self, system_config):
        """Creating record to save and send to Subscriber"""
        config_filename = bl.path+'system_config.txt'
        IoT_device_config = open(config_filename,'w')
        print >> IoT_device_config, system_config
        IoT_device_config.close()


    def read_config(self):
        """ Reading system configuration from the file """
        config = []
        config_filename = bl.path+'system_config.txt'
        IoT_device_config = open(config_filename,'r')
        config = IoT_device_config.readline()
        try:
            config = json.loads(config.replace("\'", '"'))
            self.device_id = config['Device ID']
            #self.latitude = config['Latitude']
            #self.longitude = config['Longitude']
            self.scan_interval = config['Scan Interval']
            self.transmission_flag = config['Transmission Flag']
            self.debug_flag = config['Debug Flag']
        except (ValueError, KeyError, TypeError):
            print "JSON format Error"

        IoT_device_config.close()


    def credential_setup(self):
        self.device_id = raw_input("Enter the device ID : ")
        self.system_config["Device ID"] = self.device_id
        #self.latitude = raw_input("Enter IoT device Latitude position : ")
        #self.system_config["Latitude"] = self.latitude
        #self.longitude = raw_input("Enter IoT device Longitude position : ")
        #self.system_config["Longitude"] = self.longitude
        self.scan_interval = raw_input("Enter the interval between each scan (in seconds) : ")
        self.system_config["Scan Interval"] = self.scan_interval
        self.transmission_flag = raw_input("Do you want to transmit data to subscribers (Y/N) : ")
        self.system_config["Transmission Flag"] = self.transmission_flag
        self.debug_flag = raw_input("Do you want to display debug logs (Y/N) : ")
        self.system_config["Debug Flag"] = self.debug_flag
        
        bl.save_config(self.system_config)


    def get_output(self, command, pause = 0):
        """Run a command in bluetoothctl prompt, return output as a list of lines."""
        self.child.send(command + "\n")
        time.sleep(pause)
        start_failed = self.child.expect([pexpect.TIMEOUT, "bluetooth", pexpect.EOF])

        if start_failed != 1:
            raise BluetoothctlError("Bluetoothctl failed after running " + command)

        return self.child.before.split("\r\n")


    def start_scan(self):
        """Start bluetooth scanning process."""
        try:
            out = self.get_output("scan on")
        except BluetoothctlError, e:
            print(e)
            return None


    def make_discoverable(self):
        """Make device discoverable."""
        try:
            out = self.get_output("discoverable on")
        except BluetoothctlError, e:
            print(e)
            return None


    def parse_device_info(self, info_string):
        """Parse a string corresponding to a device."""
        device = {}
        block_list = ["[\x1b[0;", "removed"]
        string_valid = not any(keyword in info_string for keyword in block_list)

        if string_valid:
            try:
                device_position = info_string.index("Device")
            except ValueError:
                pass
            else:
                if device_position > -1:
                    attribute_list = info_string[device_position:].split(" ", 2)
                    device = {
                        "mac_address": attribute_list[1],
                        "name": attribute_list[2]
                    }
        return device


    def get_available_devices(self):
        """Return a list of tuples of paired and discoverable devices."""
        
        available_devices_count = 0
        try:
            out = self.get_output("devices")
        except BluetoothctlError, e:
            print(e)
            return None
        else:
            available_devices = []
            for line in out:
                device = self.parse_device_info(line)
                if device:
                    available_devices.append(device)
                    available_devices_count = available_devices_count + 1;

            self.devices_dict["devices"] = available_devices
            self.devices_dict["available devices"] = available_devices_count
            return self.devices_dict


    def get_paired_devices(self):
        """Return a list of tuples of paired devices."""
        paired_devices_count = 0
        try:
            out = self.get_output("paired-devices")
        except BluetoothctlError, e:
            print(e)
            return None
        else:
            paired_devices = []
            for line in out:
                device = self.parse_device_info(line)
                if device:
                    paired_devices.append(device)
                    paired_devices_count = paired_devices_count + 1

            device = {"paired devices ": paired_devices_count }
            paired_devices.append(device)
            return paired_devices


    def get_discoverable_devices(self):
        """Filter paired devices out of available."""
        available = self.get_available_devices()
        paired = self.get_paired_devices()

        return [d for d in available if d not in paired]


    def get_device_info(self, mac_address):
        """Get device info by mac address."""
        try:
            out = self.get_output("info " + mac_address)
        except BluetoothctlError, e:
            print(e)
            return None
        else:
            return out


    def remove(self, mac_address):
        """Remove paired device by mac address"""
        #print("removing pair for : " + mac_address)
        try:
            out = self.get_output("remove " + mac_address, 3)
        except BluetoothctlError, e:
            print(e)
            return None
        else:
            res = self.child.expect([pexpect.TIMEOUT, "not avilable", "Device has been removed", pexpect.EOF])
            success = True if res == 2 else False        
        return success


    def scan_list_clear(self, devices_count):
        """Clearing the scan list"""
        for i in range(0, devices_count):
            mac_address = devices[i]['mac_address']
            ret = bl.remove(str(mac_address))
            if ret == False:
                #print "unable to delete ",mac_address
                continue


    def display_scan_info(self, devices_count):
        """Display required information of scanned devices on terminal"""
        for i in range(0, devices_count):
            mac_address = devices[i]['mac_address']
            device_info = bl.get_device_info(mac_address)
            #print(device_info)
            device_info_len = len(device_info)
            search = "\tRSSI"
            for j in range(1,device_info_len-1):
                parameters = {}
                parameters = device_info[j]
                #print(parameters)
                value = parameters.split(": ")
                if value[0] == search :
                    rssi = value[1]
                    print(mac_address + " : " + rssi)


    def create_message_record(self, timestamp, devices_count):
        """Creating record to save and send to Subscriber"""
        self.message_record["Device ID"] = self.device_id
        #self.message_record["Latitude"] = self.latitude
        #self.message_record["Longitude"] = self.longitude
        self.message_record["Time Stamp"] = timestamp
        self.message_record["Devices Count"] = devices_count
        self.message_record["Signatures"] = ""
        return self.message_record


    def subscriber_lookup(self,devices_count):
        """Lookup the subscriber list, which are in range"""
        subscriber = ""
        for i in range(0, devices_count):
            mac_address = devices[i]['mac_address']
            subscriber_filename = bl.path+'subscriber.txt'
            subscriberlist = open(subscriber_filename,'r')
            for line in subscriberlist:
                if line.rstrip() == mac_address:
                    subscriber = mac_address
                    break
            if (subscriber != ""):
                break
        return subscriber


    def record_transmission(self, devices_count):
        """Transmit the data, if any subscriber is in the range of IoT device"""
        subscriber = bl.subscriber_lookup(devices_count)
        if subscriber == "":
            print "No subscriber in range"
        else:
            print "subscriber in range is :",subscriber
            ret = bl.record_transmit_to_subscriber(subscriber, str(record))
            if ret == False:
                print "Unable to send data"


    def record_transmit_to_subscriber(self, subscriber, message):
        """sending device information to subscriberr"""
        server_addr = subscriber
        port = 6 #port 6 is for sending message on bluetooth
        client_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        try:
            client_socket.connect((server_addr, port))
            print("connection established")
            client_socket.send(message)
            print("data sent")
            client_socket.close()
            return True
        except Exception as e:
            print "Host is down"
            return False


if __name__ == "__main__":

    print("Init bluetooth...")
    bl = Bluetoothctl()
    scanrecord_filename = bl.path+'scanrecord.txt'
    scanrecord = open(scanrecord_filename,'w')
    print("Welcome to Pedestrian Crosswalk feature")
    config_filename = bl.path+'system_config.txt'
    print config_filename
    IoT_device_config = open(config_filename,'r')
    config = IoT_device_config.readline()
    print "Current configuration - ",config
    #config_flag = raw_input("Do you want to continue with existing configuration? (Y/N) : ")
    config_flag = "Y"
    if (config_flag == "N"):
        bl.credential_setup()
    else:
        bl.read_config()
    previous_devices_count = 0
    while 1:
        bl.start_scan()
        print("Scanning for " + str(bl.scan_interval) + " seconds...")
        for i in xrange(0, int(bl.scan_interval)):
            print ("."),
            time.sleep(1)

        print("\n")
        json_array = bl.get_available_devices()
        #print(json_array)
        devices_count = json_array['available devices']
        devices = json_array['devices']

        #skipping further processing if the device count is not changed
        if previous_devices_count == devices_count:
            print "Previous device count is ", previous_devices_count
            print "There is no change in device count"
            bl.scan_list_clear(devices_count)
            continue

        previous_devices_count = devices_count
        
        timestamp = datetime.datetime.now()
        timestamp = timestamp.strftime('%d-%b-%Y %H:%M:%S')
        #print('Date now: %s' % timestamp)
        #print("No of devices available :" + str(devices_count))

        record = bl.create_message_record(timestamp, devices_count)
        print(record)
        """Storing the record locally in a file"""
        print >>scanrecord, record

        """ Get the device information and display MAC and RSSI """
        if bl.debug_flag == "Y":
            bl.display_scan_info(devices_count)

        """record transmission to subscriber"""
        if bl.transmission_flag == "Y":
            bl.record_transmission(devices_count)

        """ Remove the pairing of all detected devices """
        bl.scan_list_clear(devices_count)

    IoT_device_config.close()
    scanrecord.close()

