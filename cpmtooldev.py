import requests
import subprocess
import platform
import os
import json

__ENDPOINT_URL__: str = "https://kayzenn.squareweb.app/api"

class CPMTooldev:
    def __init__(self, access_key) -> None:
        self.auth_token = None
        self.access_key = access_key
        self.config_file = "device_token.json"
    
    def _send_error(self, error_message, endpoint, method="POST"):
        try:
            device_name = self.get_device_name()
            payload = {
                "error_message": error_message,
                "endpoint": endpoint,
                "method": method,
                "device_name": device_name,
                "access_key": self.access_key
            }
            requests.post(f"{__ENDPOINT_URL__}/errors", json=payload, timeout=5)
        except:
            pass
    
    def load_device_name(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    return config.get("device_name")
            except:
                pass
        return None
    
    def save_device_name(self, device_name):
        try:
            config = {"device_name": device_name}
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except:
            pass
    
    def get_device_name(self):
        saved_device_name = self.load_device_name()
        if saved_device_name:
            return saved_device_name
        
        try:
            is_android = False
            try:
                if os.path.exists('/system/build.prop'):
                    is_android = True
                elif 'ANDROID_ROOT' in os.environ:
                    is_android = True
                elif hasattr(os, 'uname') and 'android' in str(os.uname()).lower():
                    is_android = True
            except:
                pass
    
            if is_android:
                device_name = None
                commands_to_try = [
                    ['getprop', 'ro.product.model'],
                    ['getprop', 'ro.product.brand'],
                    ['getprop', 'ro.product.device'],
                    ['getprop', 'ro.product.name'],
                    ['getprop', 'ro.product.manufacturer'],
                    ['getprop', 'ro.product.model'],
                ]
                
                brand = None
                model = None
                
                for cmd in commands_to_try:
                    try:
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                        output = result.stdout.strip()
                        if output and output != "":
                            if 'brand' in cmd[1]:
                                brand = output
                            elif 'model' in cmd[1]:
                                model = output
                            elif 'device' in cmd[1] and not model:
                                model = output
                            elif 'manufacturer' in cmd[1] and not brand:
                                brand = output
                    except:
                        continue
                
                if brand and model:
                    device_name = f"{brand} {model}"
                elif brand:
                    device_name = brand
                elif model:
                    device_name = model
                else:
                    device_name = "Android Device"
                    
            else:
                system = platform.system()
                if system == "Windows":
                    result = subprocess.run(['wmic', 'computersystem', 'get', 'model'], 
                                          capture_output=True, text=True, check=True)
                    device_name = result.stdout.split('\n')[1].strip()
                elif system == "Darwin":
                    result = subprocess.run(['scutil', '--get', 'ComputerName'], 
                                          capture_output=True, text=True, check=True)
                    device_name = result.stdout.strip()
                elif system == "Linux":
                    result = subprocess.run(['hostname'], 
                                          capture_output=True, text=True, check=True)
                    device_name = result.stdout.strip()
                else:
                    device_name = "Unknown Device"
            
            if not device_name or device_name == "" or device_name == "localhost":
                device_name = input("Could not detect device name. Please enter your device name manually: ")
            
            self.save_device_name(device_name)
            return device_name
            
        except Exception as e:
            device_name = input("Could not detect device name. Please enter your device name manually: ")
            self.save_device_name(device_name)
            return device_name

    def check_device(self):
        try:
            device_name = self.get_device_name()
            params = {
                "key": self.access_key,
                "device_name": device_name
            }
            response = requests.get(f"{__ENDPOINT_URL__}/check_device", params=params)
            response.raise_for_status()
            response_decoded = response.json()
            return response_decoded
        except Exception as e:
            self._send_error(str(e), "check_device", "GET")
            return {"ok": False, "error": "Device check failed"}

    def _make_request(self, endpoint, payload=None, method="POST"):
        try:
            device_check = self.check_device()
            if not device_check.get("ok"):
                return device_check
            
            if method == "POST":
                response = requests.post(f"{__ENDPOINT_URL__}/{endpoint}", params={"key": self.access_key}, json=payload)
            else:
                response = requests.get(f"{__ENDPOINT_URL__}/{endpoint}", params={"key": self.access_key})
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self._send_error(str(e), endpoint, method)
            return {"ok": False, "error": f"Request to {endpoint} failed"}

    def login(self, email, password) -> int:
        try:
            device_name = self.get_device_name()
            payload = { 
                "account_email": email, 
                "account_password": password,
                "device_name": device_name
            }
            response_decoded = self._make_request("account_login", payload)
            if response_decoded.get("ok"):
                self.auth_token = response_decoded.get("auth")
            return response_decoded.get("error")
        except Exception as e:
            self._send_error(str(e), "account_login")
            return 1

    def get_key_data(self):
        try:
            device_name = self.get_device_name()
            params = {
                "key": self.access_key,
                "device_name": device_name
            }
            response = requests.get(f"{__ENDPOINT_URL__}/get_key_data", params=params)
            response.raise_for_status()
            response_decoded = response.json()
            return response_decoded
        except Exception as e:
            self._send_error(str(e), "get_key_data", "GET")
            return {"ok": False, "error": "Failed to get key data"}

    def register(self, email, password) -> int:
        try:
            payload = { 
                "account_email": email, 
                "account_password": password
            }
            response_decoded = self._make_request("account_register", payload)
            if response_decoded.get("ok"):
                self.auth_token = response_decoded.get("auth")
            return response_decoded.get("error")
        except Exception as e:
            self._send_error(str(e), "account_register")
            return 1

    def delete(self):
        try:
            payload = { "account_auth": self.auth_token }
            response_decoded = self._make_request("account_delete", payload)
            return response_decoded.get("ok")
        except Exception as e:
            self._send_error(str(e), "account_delete")
            return False

    def get_player_data(self):
        try:
            payload = { "account_auth": self.auth_token }
            response = self._make_request("get_data", payload)
            return response
        except Exception as e:
            self._send_error(str(e), "get_data")
            return {"ok": False, "error": "Failed to get player data"}

    def set_player_rank(self):
        try:
            payload = { "account_auth": self.auth_token }
            response_decoded = self._make_request("set_rank", payload)
            return response_decoded.get("ok")
        except Exception as e:
            self._send_error(str(e), "set_rank")
            return False

    def unlock_smoke(self):
        try:
            payload = { "account_auth": self.auth_token }
            response_decoded = self._make_request("unlock_smoke", payload)
            return response_decoded.get("ok")
        except Exception as e:
            self._send_error(str(e), "unlock_smoke")
            return False

    def unlock_w16(self):
        try:
            payload = { "account_auth": self.auth_token }
            response_decoded = self._make_request("unlock_w16", payload)
            return response_decoded.get("ok")
        except Exception as e:
            self._send_error(str(e), "unlock_w16")
            return False

    def set_player_loses(self, amount):
        try:
            payload = {
                "account_auth": self.auth_token,
                "amount": amount
            }
            response_decoded = self._make_request("set_race_loses", payload)
            return response_decoded.get("ok")
        except Exception as e:
            self._send_error(str(e), "set_race_loses")
            return False

    def set_player_wins(self, amount):
        try:
            payload = {
                "account_auth": self.auth_token,
                "amount": amount
            }
            response_decoded = self._make_request("set_race_wins", payload)
            return response_decoded.get("ok")
        except Exception as e:
            self._send_error(str(e), "set_race_wins")
            return False

    def unlock_equipments_male(self):
        try:
            payload = { "account_auth": self.auth_token }
            response_decoded = self._make_request("unlock_clothes_male", payload)
            return response_decoded.get("ok")
        except Exception as e:
            self._send_error(str(e), "unlock_clothes_male")
            return False

    def unlock_equipments_female(self):
        try:
            payload = { "account_auth": self.auth_token }
            response_decoded = self._make_request("unlock_clothes_female", payload)
            return response_decoded.get("ok")
        except Exception as e:
            self._send_error(str(e), "unlock_clothes_female")
            return False

    def unlock_houses(self):
        try:
            payload = { "account_auth": self.auth_token }
            response_decoded = self._make_request("unlock_houses", payload)
            return response_decoded.get("ok")
        except Exception as e:
            self._send_error(str(e), "unlock_houses")
            return False

    def unlock_animations(self):
        try:
            payload = { "account_auth": self.auth_token }
            response_decoded = self._make_request("unlock_animations", payload)
            return response_decoded.get("ok")
        except Exception as e:
            self._send_error(str(e), "unlock_animations")
            return False

    def set_player_name(self, name):
        try:
            payload = { 
                "account_auth": self.auth_token, 
                "name": name 
            }
            response_decoded = self._make_request("set_name", payload)
            return response_decoded.get("ok")
        except Exception as e:
            self._send_error(str(e), "set_name")
            return False

    def set_player_localid(self, id):
        try:
            payload = { 
                "account_auth": self.auth_token, 
                "id": id 
            }
            response_decoded = self._make_request("set_id", payload)
            return response_decoded.get("ok")
        except Exception as e:
            self._send_error(str(e), "set_id")
            return False

    def set_player_money(self, amount):
        try:
            payload = {
                "account_auth": self.auth_token,
                "amount": amount
            }
            response_decoded = self._make_request("set_money", payload)
            return response_decoded.get("ok")
        except Exception as e:
            self._send_error(str(e), "set_money")
            return False

    def set_player_coins(self, amount):
        try:
            payload = {
                "account_auth": self.auth_token,
                "amount": amount
            }
            response_decoded = self._make_request("set_coin", payload)
            return response_decoded.get("ok")
        except Exception as e:
            self._send_error(str(e), "set_coin")
            return False

    def unlock_horns(self):
        try:
            payload = { "account_auth": self.auth_token }
            response_decoded = self._make_request("unlock_horns", payload)
            return response_decoded.get("ok")
        except Exception as e:
            self._send_error(str(e), "unlock_horns")
            return False

    def unlock_wheels(self):
        try:
            payload = { "account_auth": self.auth_token }
            response_decoded = self._make_request("unlock_wheels", payload)
            return response_decoded.get("ok")
        except Exception as e:
            self._send_error(str(e), "unlock_wheels")
            return False

    def disable_engine_damage(self):
        try:
            payload = { "account_auth": self.auth_token }
            response_decoded = self._make_request("unlock_disable_damage", payload)
            return response_decoded.get("ok")
        except Exception as e:
            self._send_error(str(e), "unlock_disable_damage")
            return False

    def unlimited_fuel(self):
        try:
            payload = { "account_auth": self.auth_token }
            response_decoded = self._make_request("unlimited_fuel", payload)
            return response_decoded.get("ok")
        except Exception as e:
            self._send_error(str(e), "unlimited_fuel")
            return False