import paramiko
import time
import os
import re

#<editor-fold desc="Establishing connection">
if __name__ == '__main__':
    ip = '172.17.13.89'
    username = 'oracle'
    password = '642362kkk'
    # ip = '172.17.12.58'
    # username = 'oracle'
    # password = 'Veeam123'
    res = {}

    # Create instance of SSHClient object
    remote_conn_pre = paramiko.SSHClient()

    # Automatically add untrusted hosts (make sure okay for security policy in your environment)
    remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # initiate SSH connection
    remote_conn_pre.connect(ip, username=username, password=password, look_for_keys=False, allow_agent=False)

    # Use invoke_shell to establish an 'interactive session'
    remote_conn = remote_conn_pre.invoke_shell()
#</editor-fold>


def oratab(remote_conn):
    remote_conn.send("cat /etc/oratab\n")
    time.sleep(5)
    output = remote_conn.recv(5000)
    oratabfile = output.decode("utf-8")
    for i in oratabfile.splitlines():
        if not i.startswith('#') and not i.startswith('['):
            splitted_line = i.rstrip().split()
            if len(splitted_line) > 0 and 'cat' not in splitted_line and 'Last' not in splitted_line:
                yield (splitted_line)
# for i in oratab(remote_conn): print(i)


def inv(remote_conn):
    remote_conn.send("locate oraInst.loc\n")
    time.sleep(2)
    output = remote_conn.recv(5000)
    invfiles = output.decode("utf-8")
    for i in invfiles.splitlines():
        if i.startswith('/'):
            pathtoinv = i.splitlines()[0]
    remote_conn.send("cat " + pathtoinv + "\n")
    time.sleep(2)
    output = remote_conn.recv(5000)
    content = output.decode("utf-8")
    for i in content.splitlines():
        if i.startswith('inventory_loc'):
            oraInventory = (re.findall('=(.*)', i))[0]
    remote_conn.send("cat " + oraInventory + "/" + "ContentsXML" + "/" + "inventory.xml" + "\n")
    time.sleep(5)
    output = remote_conn.recv(7000)
    oraInv = output.decode("utf-8")
    for i in oraInv.splitlines():
        if i.startswith('<HOME NAME'):
            yield i
# for i in inv(remote_conn): print(i)


def dbs(remote_conn):
    remote_conn.send("ll $ORACLE_HOME/dbs\n")
    time.sleep(2)
    output = remote_conn.recv(5000)
    files = output.decode("utf-8")
    for i in files.splitlines():
        if len(i) > 30 and not i.startswith("Last") and not i.startswith("["):
            yield i
# for i in dbs(remote_conn): print(i)


def get_user(remote_conn):

    remote_conn.send("sqlplus / as sysdba\n")
    time.sleep(1)
    remote_conn.send("show user\n")
    time.sleep(2)
    output = remote_conn.recv(10000)
    sqlplus = output.decode("utf-8")
    for i in sqlplus.split('\n'):
        if i.find("USER") == 0:
            res[i.lstrip('SQL>').split()[0]] = i.lstrip('SQL>').split()[2][1:-1]
    return res
# print(get_user(remote_conn))


def get_online_redo_logs(remote_conn):
    remote_conn.send("sqlplus / as sysdba\n")
    time.sleep(1)
    remote_conn.send("set linesize 3000\nselect *from v$log;\n")
    time.sleep(2)
    output = remote_conn.recv(10000)
    sqlplus = output.decode("utf-8")
    lines = sqlplus.splitlines(True)
    rng = range (0, len(lines))
    for i in rng:
        if lines[i].rstrip().find('GROUP') == 4:
            res = lines[i:i+5]
            for i in res:
                value = (i.strip())
                yield (value)
# for i in get_online_redo_logs(remote_conn): print(i)


def db_status(remote_conn):
    remote_conn.send("sqlplus / as sysdba\n")
    time.sleep(1)
    remote_conn.send("set linesize 3000\nSELECT DATABASE_STATUS FROM V$INSTANCE;\n"
                     "SELECT BANNER FROM V$VERSION WHERE BANNER LIKE 'Oracle%';\n"
                     "SELECT OPEN_MODE, LOG_MODE FROM V$DATABASE;\n")
    time.sleep(7)
    output = remote_conn.recv(10000)
    sqlplus = output.decode("utf-8")
    lines = sqlplus.splitlines(True)
    rng = range(0, len(lines))
    for i in rng:
        if lines[i].strip().find('DATABASE_STATUS') == 0:
            res = lines[i:i + 3]
            for i in res:
                yield i.strip()
            print('')
        elif lines[i].strip().find('BANNER') == 0:
            res = lines[i:i + 3]
            for i in res:
                yield i.strip()
            print('')
        elif lines[i].strip().find('OPEN_MODE') == 0:
            res = lines[i:i + 3]
            for i in res:
                yield i.strip()
            print('')
# for i in db_status(remote_conn): print(i)


def is_container(remote_conn):
    remote_conn.send("sqlplus / as sysdba\n")
    time.sleep(1)
    remote_conn.send("select name, cdb, con_id, con_dbid from v$database;\n")
                     # "SELECT BANNER FROM V$VERSION WHERE BANNER LIKE 'Oracle%';\n"
                     # "SELECT OPEN_MODE, LOG_MODE FROM V$DATABASE;\n")
    time.sleep(2)
    output = remote_conn.recv(10000)
    sqlplus = output.decode("utf-8")
    lines = sqlplus.splitlines(True)
    rng = range(0, len(lines))
    for i in rng:
        # print(lines[i].strip().find('CDB'))
        # print(lines[i].strip())
        if lines[i].strip().find('CDB') == 7:
            res = lines[i:i + 3]
            for i in res:
                yield i.strip()


def get_cont(remote_conn):
    remote_conn.send("select con_id, name from v$pdbs;\n")
    time.sleep(2)
    output = remote_conn.recv(10000)
    sqlplus = output.decode("utf-8")
    lines = sqlplus.splitlines(True)
    rng = range(0, len(lines))
    for i in rng:
        # print(lines[i].strip().find('CON_ID NAME'))
        # print(lines[i].strip())
        if lines[i].strip().find('CON_ID NAME') == 0:
            res = lines[i+2:]
            for i in res:
                if len(i.strip()) != 0 and i.strip()[0].isdigit():
                    yield i.strip()


for i in is_container(remote_conn):
    # print(i)
    if 'YES' in i:
        print("Container Database is detected")
        for i in get_cont(remote_conn):
            if i.startswith('0'): print("Instance level:", re.findall(".* (.*)", i)[0])
            elif i.startswith('1'): print("Container Database:", re.findall(".* (.*)", i)[0])
            elif i.startswith('2'): print("Seed Database:", re.findall(".* (.*)", i)[0])
            else: print("Pluggable Database:", re.findall(".* (.*)", i)[0])


# select name, cdb, con_id, con_dbid from v$database;
# if exists: select con_id, name from v$pdbs;
# select name, con_id from v$active_services where con_id != 1; - show pluggable databases
# alter session set container = pdborcl;




