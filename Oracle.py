import paramiko
import time

if __name__ == '__main__':
    # ip = '172.17.13.89'
    # username = 'oracle'
    # password = '642362kkk'
    ip = '172.17.12.58'
    username = 'oracle'
    password = 'Veeam123'
    res = {}

    # Create instance of SSHClient object
    remote_conn_pre = paramiko.SSHClient()

    # Automatically add untrusted hosts (make sure okay for security policy in your environment)
    remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # initiate SSH connection
    remote_conn_pre.connect(ip, username=username, password=password, look_for_keys=False, allow_agent=False)

    # Use invoke_shell to establish an 'interactive session'
    remote_conn = remote_conn_pre.invoke_shell()


def get_user(remote_conn):  # remote_conn type is <class 'paramiko.channel.Channel'>

    remote_conn.send("sqlplus / as sysdba\n")
    time.sleep(1)
    remote_conn.send("show user\n")
    time.sleep(2)
    output = remote_conn.recv(10000)
    # return output
    sqlplus = output.decode("utf-8")
    # return sqlplus.split('\n')
    for i in sqlplus.split('\n'):
        if i.find("USER") == 0:
            res[i.lstrip('SQL>').split()[0]] = i.lstrip('SQL>').split()[2][1:-1]
    return res

# print(get_user(remote_conn))


def get_logs(remote_conn):  # remote_conn type is <class 'paramiko.channel.Channel'>
    remote_conn.send("sqlplus / as sysdba\n")
    time.sleep(1)
    remote_conn.send("set linesize 3000\nselect *from v$log;\n")
    time.sleep(2)
    output = remote_conn.recv(10000)
    # return output
    sqlplus = output.decode("utf-8")
    lines = sqlplus.splitlines(True)
    rng = range (0, len(lines))
    newrng = range (0, 1)
    for i in rng:
        # print(i, lines[i].rstrip())
        if lines[i].rstrip().find('GROUP') == 4:
            newrng = range(i, i+5)
    for i in newrng:
        print (lines[i].rstrip())
print(get_logs(remote_conn))
