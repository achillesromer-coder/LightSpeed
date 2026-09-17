from pathlib import Path
import importlib.util,sys,tempfile,json,threading,time,socket
K=Path(__file__).resolve().parents[1]/'runtime/python/cgx_kernel.py'
spec=importlib.util.spec_from_file_location('cgx_kernel_v08',K); mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)

def free_port(socktype):
    s=socket.socket(socket.AF_INET,socktype); s.bind(('127.0.0.1',0)); p=s.getsockname()[1]; s.close(); return p

with tempfile.TemporaryDirectory() as td0:
    td=Path(td0); server=td/'server'; client=td/'client'
    mod.create_empty(server,'LAN Server'); mod.create_empty(client,'LAN Client')
    mod.provider_add(server,{'id':'lab.instrument','capabilities':['instrument.inspect','instrument.run'],'connection_types':['lan'],'trust':0.98,'permissions':['execute']})
    udp_port=free_port(socket.SOCK_DGRAM); tcp_port=free_port(socket.SOCK_STREAM); locator=f'tcp://127.0.0.1:{tcp_port}'
    canonical_before_discovery=mod.compute_content_root(client)[0]
    dholder={}
    tdsc=threading.Thread(target=lambda:dholder.setdefault('r',mod.udp_discovery_serve_once(server,'127.0.0.1',udp_port,locator,5)),daemon=True);tdsc.start();time.sleep(.05)
    discovery=mod.udp_discover(client,'127.0.0.1',udp_port,2);tdsc.join(5)
    assert discovery['ok'] and discovery['service']['locator']==locator,discovery
    assert 'instrument.run' in discovery['handshake']['capabilities']
    canonical_after_discovery=mod.compute_content_root(client)[0]
    assert canonical_before_discovery==canonical_after_discovery
    mod.connection_add(client,{'id':'lab-lan','type':'lan','locator':locator,'trust':0.95,'heartbeat_ttl_seconds':10.0,'allowed_peer_object_ids':[discovery['handshake']['object_id']]})
    mod.provider_add(client,{'id':'remote.instrument','capabilities':['instrument.run'],'connection_types':['lan'],'connection_id':'lab-lan','trust':0.95,'permissions':['execute'],'privacy_penalty':0.0})
    tholder={}
    ttcp=threading.Thread(target=lambda:tholder.setdefault('r',mod.tcp_serve_once(server,'127.0.0.1',tcp_port,5)),daemon=True);ttcp.start();time.sleep(.05)
    probe=mod.tcp_probe(client,'lab-lan',2);ttcp.join(5)
    assert probe['status']['online'] and probe['status']['identity_ok'],probe
    root_before_heartbeat=mod.compute_content_root(client)[0]
    route=mod.provider_route(client,'instrument.run',allowed_networks={'lan'},min_trust=.9)
    root_after_heartbeat=mod.compute_content_root(client)[0]
    assert route['selected'] and route['selected']['id']=='remote.instrument',route
    assert root_before_heartbeat==root_after_heartbeat
    print(json.dumps({'udp_discovery_ok':discovery['ok'],'discovered_object_id':discovery['handshake']['object_id'],'discovery_capabilities':discovery['handshake']['capabilities'],'discovery_noncanonical':canonical_before_discovery==canonical_after_discovery,'tcp_probe_online':probe['status']['online'],'identity_ok':probe['status']['identity_ok'],'selected_provider':route['selected']['id'],'live_latency_ms':route['selected']['live']['latency_ms'],'heartbeat_noncanonical':root_before_heartbeat==root_after_heartbeat,'client_verify':mod.verify(client),'server_verify':mod.verify(server)},indent=2))
