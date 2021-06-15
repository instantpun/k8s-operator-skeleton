from prometheus_client import start_http_server, Summary, Counter, Gauge
from prometheus_client import start_http_server
import random
import time
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException
import os

### Prometheus metrics ###
JOB_TIME = Summary('job_processing_seconds', 'Time spent processing request') # creates decorator/context manager
JOBS = Counter('jobs', 'Number of provisioner jobs processed by the Quay-Provisioner Operator')
INPROGRESS_JOBS = Gauge('inprogress_jobs', 'Number of quayOrgMaps in progress')
EXCEPTIONS = Counter('exceptions', 'Number of exceptions encountered while querying apis', ['category','api','function']) # labels = exception category

### Prometheus server setup ###
start_http_server(8081)

def main():
    ####> setting up config the verbose way
    # configuration = kubernetes.client.Configuration()
    # # Configure API key authorization: BearerToken
    # configuration.api_key['authorization'] = 'YOUR_API_KEY'
    # # Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
    # # configuration.api_key_prefix['authorization'] = 'Bearer'

    # # Defining host is optional and default to http://localhost
    # # Within a kubernetes pod, you can construct the API server host from the environment variables
    # if os.environ.get('KUBERNETES_SERVICE_HOST') and os.environ.get('KUBERNETES_SERVICE_PORT'):
    #     configuration.host = str(os.environ['KUBERNETES_SERVICE_HOST']) + str(os.environ['KUBERNETES_SERVICE_PORT'])


    ####> config the easy way:
    config.load_kube_config()

    # all methods on the following two objects wrap kubernetes.client.api_client.ApiClient().call_api()
    core_apis = client.CoreV1Api() 
    custom_apis = client.CustomObjectsApi() 

    w = watch.Watch()

    # api.list_secret_for_all_namespaces_with_http_info, label_selector
    for item in w.stream(core_apis.list_pod_for_all_namespaces, label_selector='tier=control-plane', timeout_seconds=0):

        # Gauge.track_inprogess() increments by 1 upon entering the with bloc and decrements by 1 on exit
        with INPROGRESS_JOBS.track_inprogress():
            
            JOBS.inc() # inc counter by 1
            
            # Summary.time() tracks processing time for each item in the stream
            with JOB_TIME.time():
                pod = item['object'] # pod is a V1Pod object

                print(pod.metadata.labels)
                print(pod.metadata.namespace)
                try: 
                    # TODO: Research of read_namespace_with_http_info() is the correct method
                    ns = core_apis.read_namespace_with_http_info(pod.metadata.namespace)
                    if ns.metadata.labels.get('quay') == 'enable':
                        # fetch custom object for quayOrgMap resource
                        try:
                            print("fetching quayOrgMap")
                            #quayOrgMap = custom_apis.get_namespaced_custom_object(group, version, namespace, plural, name)
                        except ApiException as e:
                            EXCEPTIONS.labels(api='CustomOfbjectsApi', function='get_namespaced_custom_object', source='kubernetes').inc()
                            print("Exception when calling CustomObjectsApi->get_namespaced_custom_object: %s\n" % e)
                    elif ns.metadata.labels.get('quay') == 'disable':
                        # fetch custom object for quayOrgMap resource
                        try:
                            print("fetching quayOrgMap")
                            #quayOrgMap = custom_apis.get_namespaced_custom_object(group, version, namespace, plural, name)
                        except ApiException as e:
                            EXCEPTIONS.labels(api='CustomObjectsApi', function='get_namespaced_custom_object', source='kubernetes').inc()
                            print("Exception when calling CustomObjectsApi->get_namespaced_custom_object: %s\n" % e)

                except ApiException as e:
                    EXCEPTIONS.labels(api='CoreV1Api', function='read_namespace_with_http_info', source='kubernetes').inc()
                    print("Exception when calling CoreV1Api->read_namespace_with_http_info: %s\n" % e)
                


if __name__ == '__main__':
    main()