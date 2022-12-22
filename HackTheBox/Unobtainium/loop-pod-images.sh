kubectl get pods --all-namespaces --token $(cat cadmin-token) --server https://10.10.10.235:8443 --certificate-authority ca.crt
  | grep -v NAMESPACE
  | while read line; do 
      ns=$(echo $line | awk '{print $1}'); 
      name=$(echo $line | awk '{print $2}'); 
      kubectl get pod $name -o yaml -n $ns --token $(cat cadmin-token) --server https://10.10.10.235:8443 --certificate-authority ca.crt
        | grep '  - image: '; 
    done 
  | sort -u