#!/usr/bin/env python3
"""Preliminary disposable local-tap paper journey. No venue wallet key or attestation.
Run only on reviewed workflow_dispatch/native public hosted runners after publication.
"""
import argparse
from datetime import datetime,timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shlex
import socket
import stat
import subprocess
import tarfile
import time
import tomllib
import urllib.request

TAG='v1.0.1';RULES='zr1_eyJ2IjoxfQ';TAP='zunderrehearsal/channel';FORMULA=TAP+'/zunder-guard'
CHECKS={'signed_formula_install','installed_binary_and_notices','configuration_paths','init_pairing','licence_activation',
        'service_start_stop_restart','signed_reinstall_state_preservation','uninstall_preserves_state','prior_version_upgrade'}

def need(ok):
    if not ok:raise RuntimeError('Preliminary Homebrew observation incomplete')

def digest(data):return hashlib.sha256(data).hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()

def safe_file(path,private=False):
    info=path.lstat();need(stat.S_ISREG(info.st_mode)and info.st_nlink==1 and info.st_uid==os.getuid()and not info.st_mode&(0o077 if private else 0o022))
    return path.read_bytes()

def run(argv,env,input_data=None,timeout=180):
    # Never print argv/error/output: actual licence-set transient argv is sensitive.
    value=subprocess.run([str(x)for x in argv],input=input_data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                         env=env,timeout=timeout,check=False)
    need(value.returncode==0 and len(value.stdout)<=8*1024*1024 and len(value.stderr)<=8*1024*1024)
    return value.stdout

def manifest(data):
    result={}
    for row in data.decode().splitlines():
        fields=row.split();need(len(fields)==2 and re.fullmatch('[0-9a-f]{64}',fields[0])and re.fullmatch('[A-Za-z0-9._-]+',fields[1])and '..'not in fields[1]and fields[1]not in result)
        result[fields[1]]=fields[0]
    need(0<len(result)<=256);return result

def get_json(url):
    need(url.startswith('https://api.github.com/repos/zunderlabs/zunder-guard/')or url=='https://api.hyperliquid.xyz/info')
    request=urllib.request.Request(url,headers={'User-Agent':'zunder-homebrew-preliminary/1'})
    with urllib.request.urlopen(request,timeout=20)as response:
        data=response.read(2*1024*1024+1);need(len(data)<=2*1024*1024);return json.loads(data)

def stable_prior(releases):
    need(type(releases)is list);current=(1,0,1);found=[]
    for release in releases:
        need(type(release)is dict and type(release.get('draft'))is bool and type(release.get('prerelease'))is bool)
        if release['draft']or release['prerelease']:continue
        name=release.get('tag_name');need(type(name)is str)
        match=re.fullmatch(r'v([0-9]+)\.([0-9]+)\.([0-9]+)',name);need(match is not None)
        if tuple(map(int,match.groups()))<current:found.append(name)
    return found

def prior_history():
    releases=[]
    for page in range(1,11):
        batch=get_json('https://api.github.com/repos/zunderlabs/zunder-guard/releases?per_page=100&page='+str(page))
        need(type(batch)is list);releases.extend(batch)
        if len(batch)<100:return stable_prior(releases)
    raise RuntimeError('Complete public stable history could not be established')

def paper_preflight(account):
    def info(kind):
        req=urllib.request.Request('https://api.hyperliquid.xyz/info',data=json.dumps({'type':kind,'user':account}).encode(),headers={'Content-Type':'application/json'},method='POST')
        with urllib.request.urlopen(req,timeout=20)as response:return json.loads(response.read(2*1024*1024))
    need(info('userAbstraction')=='disabled')
    equity=Decimal(info('clearinghouseState')['marginSummary']['accountValue']);need(equity.is_finite()and equity>0)

def readiness(value,account,now_ms):
    sync=value.get('last_sync_ms');started=value.get('started_at_ms')
    need(value.get('version')=='1.0.1'and value.get('mode')=='paper'and value.get('network')=='mainnet'and value.get('account','').lower()==account.lower())
    need(type(sync)is int and type(started)is int and 0<started<=sync<=now_ms+5000 and now_ms-sync<=30000)
    equity=Decimal(str(value.get('equity')));need(equity.is_finite()and equity>0)
    need(value.get('risk',{}).get('state')=='active'and value['risk'].get('journal_ready')is True and value.get('journal_broken')is False and value.get('killed')is None)
    need(value.get('rules')==RULES)
    return value

def licensed(value,now_ms):
    licence=value.get('licence',{});need(licence.get('state')=='active'and type(licence.get('expires_at_ms'))is int and licence['expires_at_ms']>now_ms)
    need(value.get('fee',{}).get('mode')=='fee_free')

def mcp(binary,key,port,env,negative=False):
    method='place_order'if negative else'account_overview'
    args={'coin':'BTC','side':'buy','stop':'guard_policy','size':'0.00001'}if negative else{}
    messages=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'homebrew-preliminary','version':'1'}}},
              {'jsonrpc':'2.0','method':'notifications/initialized'},
              {'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':method,'arguments':args}}]
    data=b''.join(json.dumps(v).encode()+b'\n'for v in messages)
    answer=run([binary,'mcp','--network','paper','--guard-url','http://127.0.0.1:'+str(port),'--key-file',key],env,data,90)
    rows=[json.loads(row)for row in answer.splitlines()];reply=[v for v in rows if v.get('id')==2];need(len(reply)==1)
    result=reply[0].get('result',{});body=result.get('structuredContent',{})
    if negative:need(result.get('isError')is True and body.get('error',{}).get('code')=='client_not_registered'and body.get('ok')is False)
    else:need(result.get('isError')is False and body.get('ok')is True and body.get('guard',{}).get('client_key_registered')is True)
    return True

def tree_snapshot(home):
    result={}
    for path in sorted(home.rglob('*')):
        need(not path.is_symlink())
        if path.is_file():result[str(path.relative_to(home))]=digest(safe_file(path,True))
        else:need(path.is_dir()and path.stat().st_uid==os.getuid()and not path.stat().st_mode&0o077)
    need('guard.toml'in result and 'risk-paper.jsonl'in result and (home/'risk-paper.jsonl').stat().st_size>0)
    return result

def service_definition(home,binary,env):
    mac=platform.system()=='Darwin';base=Path.home()/('Library/LaunchAgents'if mac else'.config/systemd/user')
    candidates=[p for p in base.glob('*zunder-guard*')if p.suffix==('.plist'if mac else'.service')]
    need(len(candidates)==1);path=candidates[0];data=safe_file(path)
    if mac:
        import plistlib
        value=plistlib.loads(data);need(value.get('ProgramArguments')==[str(binary),'run','--network','paper'])
        need(value.get('EnvironmentVariables',{}).get('ZUNDER_GUARD_HOME')==str(home));label=value['Label']
        need(label in ('homebrew.mxcl.zunder-guard','sh.brew.zunder-guard'))
        text=run(['/bin/launchctl','print','gui/'+str(os.getuid())+'/'+label],env).decode();match=re.search(r'\bpid = (\d+)',text);need(match)
        pid=int(match.group(1));need(run(['/bin/ps','-p',str(pid),'-o','comm='],env).decode().strip()in (str(binary),str(binary.resolve())))
    else:
        text=data.decode();need(re.search(r'^ExecStart='+re.escape(str(binary))+r' run --network paper$',text,re.M))
        environments=[shlex.split(line.split('=',1)[1])for line in text.splitlines()if line.startswith('Environment=')]
        need(any('ZUNDER_GUARD_HOME='+str(home)in row for row in environments))
        output=run(['systemctl','--user','show',path.name,'--property=MainPID,ActiveState,FragmentPath'],env).decode()
        props=dict(line.split('=',1)for line in output.splitlines()if'='in line)
        need(props.get('ActiveState')=='active'and props.get('FragmentPath')==str(path));pid=int(props['MainPID'])
        need(Path('/proc/'+str(pid)+'/exe').resolve()==binary.resolve())
    need(pid>1);return pid,path

def stopped(port):
    with socket.socket()as sock:
        sock.settimeout(1);need(sock.connect_ex(('127.0.0.1',port))!=0)

def service_stopped(path,pid,port,env):
    stopped(port);need(not path.exists())
    if platform.system()=='Darwin':
        label=path.stem;need(label in ('homebrew.mxcl.zunder-guard','sh.brew.zunder-guard'))
        result=subprocess.run(['/bin/launchctl','print','gui/'+str(os.getuid())+'/'+label],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,timeout=15,check=False)
        need(result.returncode==113 and b'Could not find service'in result.stderr)
        process=subprocess.run(['/bin/ps','-p',str(pid),'-o','comm='],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,timeout=15,check=False)
        need(process.returncode!=0 and not process.stdout.strip())
    else:
        result=subprocess.run(['systemctl','--user','show',path.name,'--property=LoadState,MainPID,ActiveState,FragmentPath'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,timeout=15,check=False)
        values=dict(line.split('=',1)for line in result.stdout.decode().splitlines()if'='in line)
        need(values.get('LoadState')=='not-found'and values.get('MainPID')=='0'and values.get('ActiveState')=='inactive')
        need(not Path('/proc/'+str(pid)).exists())

def main():
    os.umask(0o077)
    # Job environment secret is consumed once; never inherited by subprocesses.
    licence=os.environ.pop('GUARD_PRELIM_LICENCE','').strip();account=os.environ.pop('GUARD_PRELIM_ACCOUNT','').strip()
    need(licence.startswith('zgl1_')and re.fullmatch('0x[0-9a-fA-F]{40}',account))
    parser=argparse.ArgumentParser();parser.add_argument('--assets',type=Path,required=True);parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--source',required=True);parser.add_argument('--manifest-sha256',required=True);args=parser.parse_args()
    need(os.environ.get('GITHUB_EVENT_NAME')=='workflow_dispatch'and os.environ.get('GITHUB_REPOSITORY')=='zunderlabs/homebrew-tap'and os.environ.get('GITHUB_REF')=='refs/heads/main')
    machine=platform.machine();osname=platform.system();route={('Darwin','arm64'):'darwin-arm64',('Linux','x86_64'):'linux-amd64',('Linux','aarch64'):'linux-arm64'}.get((osname,machine));need(route and os.getuid()!=0)
    need(re.fullmatch('[0-9a-f]{40}',args.source)and re.fullmatch('[0-9a-f]{64}',args.manifest_sha256))
    need(args.work.is_absolute()and not args.work.exists()and not args.work.is_symlink());args.work.mkdir(mode=0o700)
    report={'schema':1,'kind':'preliminary-local-tap-observations','route':route+'-homebrew','source':args.source,'tag':TAG,'manifest_sha256':args.manifest_sha256,'hosted_runner_native_architecture':machine,'checks':{},'browser_ui_exercised':False,'signed_exchange_authentication_exercised':False,'release_ready':False,'cleanup_complete':False}
    def record(name,observation,result='passed'):report['checks'][name]={'result':result,'observed_at':utc(),'observation':observation}
    env=dict(os.environ,HOMEBREW_NO_AUTO_UPDATE='1',HOMEBREW_NO_INSTALL_CLEANUP='1',HOMEBREW_NO_ANALYTICS='1',HOMEBREW_CACHE=str(args.work/'cache'))
    env.pop('GH_TOKEN',None);env.pop('GITHUB_TOKEN',None)
    brew='brew';prefix=Path(run([brew,'--prefix'],env).decode().strip());home=prefix/'var/zunder-guard';binary=prefix/'opt/zunder-guard/bin/zunder-guard';port=18137
    # owned_service means an admitted namespace MAY contain a live service.
    # Set before each start mutation; clear only after observed complete stop.
    owned_package=False;owned_service=False;service_path=None;tap_added=False
    try:
        need(prefix==Path('/opt/homebrew'if osname=='Darwin'else'/home/linuxbrew/.linuxbrew'))
        need(not home.exists()and not home.is_symlink()and not(prefix/'var/log/zunder-guard.log').exists()and not binary.exists())
        need(not run([brew,'list','--formula'],env).decode().splitlines().count('zunder-guard'))
        need(TAP not in run([brew,'tap'],env).decode().splitlines());stopped(port)
        for base in (Path.home()/'Library/LaunchAgents',Path('/Library/LaunchDaemons'),Path.home()/'.config/systemd/user',Path('/etc/systemd/system')):
            need(not list(base.glob('*zunder-guard*')))
        public=get_json('https://api.github.com/repos/zunderlabs/zunder-guard/releases/tags/'+TAG)
        need(public.get('tag_name')==TAG and public.get('draft')is False and public.get('prerelease')is False and public.get('published_at'))
        need(datetime.fromisoformat(public['published_at'].replace('Z','+00:00'))<=datetime.now(timezone.utc))
        report['release_id']=public['id'];report['published_at']=public['published_at']
        prior=prior_history();need(not prior) # Existing public stable requires genuine upgrade route; never invent N/A.
        record('prior_version_upgrade','Complete public stable release history has no lower stable release; current selected version excluded.','not_applicable:first_release')
        verified=json.loads(safe_file(args.assets/'.verified-release-source.json'));need(verified=={'tag':TAG,'source':args.source})
        sums=safe_file(args.assets/'SHA256SUMS');need(digest(sums)==args.manifest_sha256);subjects=manifest(sums)
        formula=safe_file(args.assets/'zunder-guard.rb');need(digest(formula)==subjects['zunder-guard.rb'])
        archive=args.assets/('zunder-guard-'+TAG+'-'+route+'.tar.gz');need(digest(safe_file(archive))==subjects[archive.name])
        paper_preflight(account)
        tap=args.work/'local-tap';(tap/'Formula').mkdir(parents=True,mode=0o700);(tap/'Formula/zunder-guard.rb').write_bytes(formula)
        run(['git','init',str(tap)],env);run(['git','-C',str(tap),'add','Formula/zunder-guard.rb'],env)
        run(['git','-C',str(tap),'-c','user.name=Channel rehearsal','-c','user.email=channel-rehearsal@invalid','commit','-m','Verify exact signed public formula'],env)
        run([brew,'tap','--custom-remote',TAP,str(tap)],env);tap_added=True
        installed_tap=Path(run([brew,'--repo',TAP],env).decode().strip());need(digest(safe_file(installed_tap/'Formula/zunder-guard.rb'))==subjects['zunder-guard.rb'])
        cache=args.work/'cache';need(not cache.exists());cache.mkdir(mode=0o700)
        run([brew,'audit','--strict','--online',FORMULA],env,timeout=600)
        owned_package=True;run([brew,'install',FORMULA],env,timeout=600);run([brew,'test',FORMULA],env)
        record('signed_formula_install','Authenticated unchanged public signed formula installed via disposable local tap with fresh unseeded cache; not official tap command.')
        need(b'1.0.1'in run([binary,'--version'],env))
        expected={'zunder-guard':binary,'LICENSE':prefix/'opt/zunder-guard/share/zunder-guard/LICENSE','NOTICE':prefix/'opt/zunder-guard/share/zunder-guard/NOTICE','THIRD_PARTY_LICENSES.md':prefix/'opt/zunder-guard/share/zunder-guard/THIRD_PARTY_LICENSES.md'}
        with tarfile.open(archive,'r:gz')as tar:
            for name,destination in expected.items():
                members=[m for m in tar.getmembers()if Path(m.name).name==name];need(len(members)==1 and members[0].isfile()and members[0].size<100*1024*1024)
                stream=tar.extractfile(members[0]);need(stream is not None)
                with stream:need(digest(stream.read())==digest(safe_file(destination)))
        record('installed_binary_and_notices','Actual native installed version, executable and three notices match signed archive regular members byte for byte.')
        env['ZUNDER_GUARD_HOME']=str(home);client=args.work/'client'
        run([binary,'init','--non-interactive','--network','paper','--account',account,'--listen','127.0.0.1:'+str(port),'--rules',RULES,'--client-key-out',client],env,timeout=180)
        pairing=run([binary,'pair'],env).decode();codes=re.findall(r'zgp1_([0-9a-f]{32})',pairing);secrets=re.findall(r'^\s*(0x[0-9a-f]{64})\s*$',pairing,re.M)
        need(len(codes)==1 and len(secrets)==1);client2=args.work/'client-paired';client2.write_text(secrets[0]+'\n');client2.chmod(0o600)
        config=tomllib.loads(safe_file(home/'guard.toml',True).decode())
        need(config.get('mode')=='paper'and config.get('network')=='mainnet'and config.get('listen')=='127.0.0.1:'+str(port)and config.get('account','').lower()==account.lower())
        state_dir=Path(config['state_dir']);state_dir=state_dir if state_dir.is_absolute()else home/state_dir;need(state_dir.resolve()==home.resolve())
        need(config.get('licence_auto_update',False)is False)
        need(config.get('pairing_sha3')==hashlib.sha3_256(('zgp1_'+codes[0]).encode()).hexdigest());del pairing,secrets,codes
        run([binary,'check-config'],env)
        record('configuration_paths','Actual paper/mainnet-public-data config, formula var home, loopback listen, resolved state directory and installed CLI agree.')
        run([binary,'licence','set',licence],env,timeout=180);licence=''
        owned_service=True;run([brew,'services','start','zunder-guard'],env)
        def ready():
            end=time.monotonic()+120
            while time.monotonic()<end:
                try:
                    status=json.loads(run([binary,'status','--json'],env,timeout=15));readiness(status,account,int(time.time()*1000));licensed(status,int(time.time()*1000));return status
                except (RuntimeError,ValueError,TypeError,KeyError,ArithmeticError):time.sleep(1)
            raise RuntimeError('Fresh licensed paper readiness not observed')
        status=ready();pid,service_path=service_definition(home,binary,env)
        need(mcp(binary,client2,port,env));unknown=args.work/'unregistered-client';unknown.write_text('0x'+os.urandom(32).hex()+'\n');unknown.chmod(0o600);need(mcp(binary,unknown,port,env,True))
        record('init_pairing','Real CLI init/pair changed actual pairing hash and registered new client; shipped MCP account_overview confirms registration; unregistered Guard-only client place_order refused before exchange. No browser UI or signed exchange authentication claim.')
        run([binary,'licence','show'],env);record('licence_activation','Existing real paid account-bound licence actually reports active/unexpired and fee_free in running paper Guard; no purchase or builder-fee substitution.')
        config_before=digest(safe_file(home/'guard.toml',True));start=status['started_at_ms']
        run([brew,'services','restart','zunder-guard'],env);status=ready();pid2,service_path=service_definition(home,binary,env)
        need(pid2!=pid and status['started_at_ms']>start and digest(safe_file(home/'guard.toml',True))==config_before);need(mcp(binary,client2,port,env))
        run([brew,'services','stop','zunder-guard'],env)
        need(service_path is not None);service_stopped(service_path,pid2,port,env);owned_service=False
        record('service_start_stop_restart','Actual generated user service points to installed signed binary/run paper/real home; distinct observed process/start, fresh licensed sync and unchanged config/client; stopped job file and listener absent.')
        checkpoint=tree_snapshot(home);run([brew,'reinstall',FORMULA],env,timeout=600);need(tree_snapshot(home)==checkpoint)
        owned_service=True;run([brew,'services','start','zunder-guard'],env);ready();pid3,service_path=service_definition(home,binary,env);need(mcp(binary,client2,port,env))
        run([brew,'services','stop','zunder-guard'],env);service_stopped(service_path,pid3,port,env);owned_service=False
        record('signed_reinstall_state_preservation','Actual same signed version reinstall preserved every stopped private home file exactly, then real readiness/licence/client connection resumed. No fabricated decision rows or padding-as-logical-history claim.')
        checkpoint=tree_snapshot(home);run([brew,'uninstall','zunder-guard'],env);owned_package=False
        need(tree_snapshot(home)==checkpoint and not binary.exists()and not service_path.exists())
        need(not(prefix/'opt/zunder-guard').exists()and not(prefix/'opt/zunder-guard').is_symlink())
        need('zunder-guard'not in run([brew,'list','--formula'],env).decode().splitlines());stopped(port)
        record('uninstall_preserves_state','Actual uninstall removed formula/executable/user-job/listener while exact stopped config/licence/client/risk/decision files remain byte-identical in owned var home.')
        run([brew,'untap',TAP],env);tap_added=False
        need(set(report['checks'])==CHECKS);report['nine_observations_completed']=True
    except BaseException:
        report['nine_observations_completed']=False;report['failure']='Observation incomplete; private details withheld'
        raise
    finally:
        # Hosted disposable VM retains private home until provider disposal. No secure-erasure claim.
        # Never stop an unrecognized job. A mismatch is preserved as pending for root review.
        if owned_service:
            try:
                final_pid,final_path=service_definition(home,binary,env);run([brew,'services','stop','zunder-guard'],env);service_stopped(final_path,final_pid,port,env);owned_service=False
            except BaseException:report['owned_service_cleanup_pending']=True
        report['owned_service_stopped']=not owned_service
        report['owned_package_present']=owned_package;report['owned_local_tap_present']=tap_added
        report['private_state_retained_until_hosted_vm_disposal']=True
        (args.work/'observations.json').write_text(json.dumps(report,indent=2)+'\n')
        # No raw output, config, licence, client key or pairing code is ever uploaded.

if __name__=='__main__':
    try:main()
    except BaseException:
        print('Preliminary Homebrew journey incomplete; consult redacted observations only.');raise SystemExit(1)
