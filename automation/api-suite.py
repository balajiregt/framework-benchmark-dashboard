"""Start an isolated sample API, run its existing oracle and normalize its JUnit evidence."""
import os,pathlib,signal,socket,subprocess,time,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[2]
SERVICE=ROOT/'projects/microservices/xyz-service'
XML=ROOT/'projects/microservices/qa-projects/xyz-service-api-tests/target/surefire-reports/TEST-com.agentic.workspace.qa.xyz.tests.CustomerRiskApiTest.xml'
def stop(signum,frame): raise KeyboardInterrupt
signal.signal(signal.SIGTERM,stop)
def main():
    with socket.socket() as port:port.bind(('127.0.0.1',4283))
    XML.unlink(missing_ok=True)
    log=ROOT/'benchmark-results/api-service.log'
    with log.open('w') as output:
        service=subprocess.Popen(['mvn','spring-boot:run','-Dspring-boot.run.arguments=--server.port=4283 --server.address=127.0.0.1'],cwd=SERVICE,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            for _ in range(180):
                if service.poll() is not None:raise RuntimeError('Sample API exited before readiness')
                try:
                    with urllib.request.urlopen('http://127.0.0.1:4283/actuator/health',timeout=1) as response:
                        if response.status==200:break
                except OSError:pass
                time.sleep(1)
            else:raise RuntimeError('Sample API readiness timed out')
            result=subprocess.run(['mvn','-pl','qa-projects/xyz-service-api-tests','-am','test','-Dapi.port=4283'],cwd=ROOT/'projects/microservices',timeout=600)
            normalized=subprocess.run(['python3','benchmarks/junit_to_report.py','benchmark-results/api-oracle.json',str(XML)],cwd=ROOT)
            return result.returncode or normalized.returncode
        finally:
            if service.poll() is None:
                os.killpg(service.pid,signal.SIGTERM)
                try:service.wait(timeout=10)
                except subprocess.TimeoutExpired:os.killpg(service.pid,signal.SIGKILL);service.wait()
if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception:print('API benchmark could not complete; inspect the ignored local service log.');raise SystemExit(1)
