"""Reference feasibility checks; never count these authored solutions as agent trials."""
import argparse,pathlib,json
from engine import *
from campaign import awake
p=argparse.ArgumentParser();p.add_argument('--api',type=pathlib.Path,required=True);p.add_argument('--harness',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
base=a.output.resolve()
if base.exists():raise ValueError('Use a new reference directory; retain prior preflights')
base.mkdir(parents=True);tasks=read(ROOT/'tasks.json')['tasks'];sources={'api':a.api.resolve(),'harness':a.harness.resolve()};results=[]
with awake(),api.service(sources['api'],base) as proxy,ui_service(sources['harness'],base):
 for t in tasks:
  if t['operation']=='validate':continue
  folder=base/t['id'];folder.mkdir();w=folder/'workspace';project(sources[t['project']],w,t,'baseline')
  if t['project']=='api':
   f=w/t['evidence'][0];s=f.read_text()
   if t['operation']=='create':
    code='''
  @Test
  void normalizesWhitespaceAndCase() {
    var response = given(requestSpec).queryParam("customerId", " cust-1001 ").when().get("/xyz").then().statusCode(200);
    hasField(response, "customerId", "CUST-1001");
    hasField(response, "eligible", true);
    hasField(response, "riskCategory", "LOW");
    hasField(response, "score", 18);
    hasField(response, "decisionReason", "Customer is eligible with low risk signals.");
  }
''';s=s.rsplit('}',1)[0]+code+'}\n'
   else:s=s.replace('.body("riskCategory", equalTo("HIGH"));','.body("riskCategory", equalTo("HIGH"))\n        .body("score", equalTo(91))\n        .body("decisionReason", equalTo("Customer requires manual review before eligibility."));')
   f.write_text(s);r=api.verify(w,folder)
  else:
   f=w/'tests/sample-crm.spec.ts';s=f.read_text()
   if t['operation']=='create':s+='''

test('viewer direct Leads and Reports denial @crm', async ({sampleCrmPage, sampleCrmAssertions}) => {
  await sampleCrmPage.gotoLogin();
  await sampleCrmPage.signInAs('viewer');
  await sampleCrmPage.gotoLeads();
  await sampleCrmAssertions.expectPermissionDeniedForPath('/crm/leads');
  await sampleCrmPage.gotoReports();
  await sampleCrmAssertions.expectPermissionDeniedForPath('/crm/reports');
});
'''
   else:
    s=s.replace("import { test }", "import { test, expect }")
    s=s.replace('await sampleCrmAssertions.expectViewerAccountsReadOnly();', '''await sampleCrmAssertions.expectViewerAccountsReadOnly();
    const response = await sampleCrmPage.page.request.get('/api/accounts/export');
    expect(response.status()).toBe(403);
    expect(await response.json()).toEqual({ error: 'Access denied' });''')
   f.write_text(s);r=ui_verify(w,folder)
  write(folder/'verification.json',r);results.append({'task':t['id'],'passed':r['passed'],'cases':len(r['cases']),'elapsedMs':r['elapsedMs']});print(json.dumps(results[-1]),flush=True)
write(base/'summary.json',{'classification':'supervising-assistant-authored reference feasibility checks, not model trials','results':results})
if not all(r['passed'] for r in results):raise SystemExit(1)
