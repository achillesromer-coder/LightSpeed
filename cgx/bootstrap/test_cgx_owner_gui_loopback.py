"""Loopback review safety negatives. No real household network scans."""
import unittest
from cgx_owner_gui_loopback import gate,COOKIE,PORT
class LocalPremintGateTest(unittest.TestCase):
    def setUp(self):
        self.ticket="a"*64
        self.host=f"127.0.0.1:{PORT}"
        self.cookie=f"{COOKIE}={self.ticket}"
    def test_cookie_required_for_every_asset(self):
        self.assertEqual(gate("GET","/assets/app.js",self.host,"",self.ticket),"DENY_SESSION")
        self.assertEqual(gate("GET","/review/source.json",self.host,"",self.ticket),"DENY_SESSION")
        self.assertEqual(gate("GET","/data/private.json",self.host,self.cookie,self.ticket),"ALLOW_STATIC")
    def test_wrong_host_and_remote_network_are_denied(self):
        for host in ["192.168.1.10:4174","my-laptop:4174","0.0.0.0:4174","[::1]:4174"]:
            self.assertEqual(gate("GET","/",host,self.cookie,self.ticket),"DENY_HOST")
    def test_token_hijack_and_path_crossing_denied(self):
        self.assertEqual(gate("GET","/start?ticket=bad",self.host,"",self.ticket),"DENY_TICKET")
        self.assertEqual(gate("GET","/start?ticket="+self.ticket,self.host,"",self.ticket),"START_SESSION")
        self.assertEqual(gate("GET","/../private",self.host,self.cookie,self.ticket),"DENY_PATH")
        self.assertEqual(gate("GET","/.git/config",self.host,self.cookie,self.ticket),"DENY_PATH")
        self.assertEqual(gate("GET","/api/state",self.host,self.cookie,self.ticket),"DENY_API")
        self.assertEqual(gate("GET","/",self.host,"badcookie",self.ticket),"DENY_SESSION")
    def test_no_browser_mutation_methods(self):
        for method in ["POST","PUT","PATCH","DELETE","OPTIONS"]:
            self.assertEqual(gate(method,"/",self.host,self.cookie,self.ticket),"DENY_METHOD")
if __name__=="__main__":
    unittest.main()
