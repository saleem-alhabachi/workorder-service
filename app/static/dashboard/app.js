document.addEventListener('DOMContentLoaded', () => {
    // UI Elements
    const emptyState = document.getElementById('empty-state');
    const endpointView = document.getElementById('endpoint-view');
    const sidebarEndpoints = document.getElementById('sidebar-endpoints');
    const routeSearch = document.getElementById('routeSearch');
    
    // Auth & Tests
    const activeTokenInput = document.getElementById('activeToken');
    const tokenResult = document.getElementById('tokenResult');
    const authHeaderInput = document.getElementById('auth-header-input');
    
    // Main Workspace
    const epMethod = document.getElementById('ep-method');
    const epName = document.getElementById('ep-name');
    const epDesc = document.getElementById('ep-desc');
    const urlEditor = document.getElementById('url-editor');
    const btnExecute = document.getElementById('btn-execute');
    
    // Params
    const pathParamsContainer = document.getElementById('path-params-container');
    const queryParamsContainer = document.getElementById('query-params-container');
    const noParamsMsg = document.getElementById('no-params-msg');
    const pathParamsTableBody = document.querySelector('#path-params-table tbody');
    const queryParamsTableBody = document.querySelector('#query-params-table tbody');
    
    // Body
    const bodySchemaInfo = document.getElementById('body-schema-info');
    const bodyEditor = document.getElementById('body-editor');
    
    // Response & Snippets
    const responseViewer = document.getElementById('response-viewer');
    const resStatus = document.getElementById('res-status');
    const resTime = document.getElementById('res-time');
    const responseMeta = document.getElementById('response-meta');
    const snippetViewer = document.getElementById('snippet-viewer');
    const snippetLang = document.getElementById('snippet-lang');

    let openApiSpec = null;
    let currentEndpoint = null; // { path, method, spec }

    // --- Tab Switching Logic ---
    function setupTabs(tabSelector, contentSelector, activeClass = 'active') {
        const tabs = document.querySelectorAll(tabSelector);
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const targetId = tab.getAttribute('data-target');
                const siblings = tab.parentElement.querySelectorAll(tabSelector);
                siblings.forEach(t => t.classList.remove(activeClass));
                tab.classList.add(activeClass);
                
                // Content switching: assuming contents are siblings sharing a common parent class or ID prefix
                // Simpler: just hide all contentSelector elements that are relevant
                // For sidebar, they are all .nav-content
                // For req/res, they are inside specific parents. 
                // Let's just find the parent and toggle children matching contentSelector
                const container = document.getElementById(targetId).parentElement;
                container.querySelectorAll(contentSelector).forEach(c => c.classList.remove(activeClass));
                document.getElementById(targetId).classList.add(activeClass);
                
                if (contentSelector === '.res-content') updateSnippets();
            });
        });
    }

    setupTabs('.sidebar-tab', '.nav-content');
    setupTabs('.req-tab', '.req-content');
    setupTabs('.res-tab', '.res-content');

    // --- Init OpenAPI ---
    async function init() {
        try {
            const res = await fetch('/openapi.json');
            openApiSpec = await res.json();
            renderSidebar();
        } catch (e) {
            console.error('Failed to load OpenAPI spec', e);
            sidebarEndpoints.innerHTML = '<div style="color:var(--accent-red); padding: 12px;">Failed to load OpenAPI spec. Is the API running?</div>';
        }
    }

    function renderSidebar(filter = '') {
        sidebarEndpoints.innerHTML = '';
        if (!openApiSpec || !openApiSpec.paths) return;

        filter = filter.toLowerCase();

        Object.keys(openApiSpec.paths).forEach(path => {
            const methods = openApiSpec.paths[path];
            Object.keys(methods).forEach(method => {
                const spec = methods[method];
                
                if (filter && !path.toLowerCase().includes(filter) && !(spec.summary || '').toLowerCase().includes(filter)) {
                    return;
                }

                const el = document.createElement('div');
                el.className = 'ep-item';
                el.innerHTML = `
                    <span class="ep-method-badge method-${method.toUpperCase()}">${method.toUpperCase()}</span>
                    <span class="ep-path" title="${path}">${path}</span>
                `;
                
                el.addEventListener('click', () => {
                    document.querySelectorAll('.ep-item').forEach(i => i.classList.remove('active'));
                    el.classList.add('active');
                    loadEndpoint(path, method, spec);
                });

                sidebarEndpoints.appendChild(el);
            });
        });
    }

    routeSearch.addEventListener('input', (e) => renderSidebar(e.target.value));

    // --- Load Endpoint ---
    function loadEndpoint(path, method, spec) {
        currentEndpoint = { path, method, spec };
        emptyState.classList.add('hidden');
        endpointView.classList.remove('hidden');

        epMethod.textContent = method.toUpperCase();
        epMethod.className = `method-badge method-${method.toUpperCase()}`;
        epName.textContent = spec.summary || path;
        epDesc.textContent = spec.description || 'No description provided.';
        urlEditor.value = path;

        // Reset Response
        responseViewer.textContent = "Hit 'Send' to execute request.";
        responseMeta.classList.add('hidden');

        // Parse Params
        pathParamsTableBody.innerHTML = '';
        queryParamsTableBody.innerHTML = '';
        pathParamsContainer.classList.add('hidden');
        queryParamsContainer.classList.add('hidden');
        noParamsMsg.classList.remove('hidden');
        
        let hasParams = false;

        if (spec.parameters && spec.parameters.length > 0) {
            spec.parameters.forEach(p => {
                hasParams = true;
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${p.name} ${p.required ? '<span style="color:var(--accent-red)">*</span>' : ''}</td>
                    <td><input type="text" data-param-in="${p.in}" data-param-name="${p.name}" placeholder="${p.schema?.type || 'string'}"></td>
                `;
                
                if (p.in === 'path') {
                    pathParamsTableBody.appendChild(tr);
                    pathParamsContainer.classList.remove('hidden');
                    noParamsMsg.classList.add('hidden');
                } else if (p.in === 'query') {
                    queryParamsTableBody.appendChild(tr);
                    queryParamsContainer.classList.remove('hidden');
                    noParamsMsg.classList.add('hidden');
                }
                
                // Add event listener to update URL live
                tr.querySelector('input').addEventListener('input', updateUrlAndSnippets);
            });
        }

        // Parse Body
        bodyEditor.value = '';
        bodySchemaInfo.textContent = 'Schema: N/A';
        const content = spec.requestBody?.content;
        if (content && content['application/json']) {
            const schemaRef = content['application/json'].schema?.$ref;
            if (schemaRef) {
                const schemaName = schemaRef.split('/').pop();
                bodySchemaInfo.textContent = `Schema: ${schemaName}`;
                
                // Attempt to generate dummy JSON
                if (openApiSpec.components && openApiSpec.components.schemas && openApiSpec.components.schemas[schemaName]) {
                    const props = openApiSpec.components.schemas[schemaName].properties || {};
                    const dummy = {};
                    Object.keys(props).forEach(k => {
                        dummy[k] = props[k].type === 'string' ? "string" : (props[k].type === 'integer' ? 0 : null);
                    });
                    bodyEditor.value = JSON.stringify(dummy, null, 2);
                }
            } else {
                bodySchemaInfo.textContent = 'Schema: JSON';
                bodyEditor.value = '{\n  \n}';
            }
        }
        
        bodyEditor.addEventListener('input', updateSnippets);

        updateUrlAndSnippets();
    }

    // --- Live Execution Engine ---
    function getCompiledUrl() {
        if (!currentEndpoint) return '';
        let url = currentEndpoint.path;
        
        // Path params
        document.querySelectorAll('input[data-param-in="path"]').forEach(input => {
            const val = input.value;
            if (val) {
                url = url.replace(`{${input.getAttribute('data-param-name')}}`, encodeURIComponent(val));
            }
        });
        
        // Query params
        const qp = [];
        document.querySelectorAll('input[data-param-in="query"]').forEach(input => {
            const val = input.value;
            if (val) {
                qp.push(`${encodeURIComponent(input.getAttribute('data-param-name'))}=${encodeURIComponent(val)}`);
            }
        });
        
        if (qp.length > 0) {
            url += '?' + qp.join('&');
        }
        
        return url;
    }

    function updateUrlAndSnippets() {
        urlEditor.value = getCompiledUrl();
        updateSnippets();
    }

    btnExecute.addEventListener('click', async () => {
        if (!currentEndpoint) return;
        
        const method = currentEndpoint.method.toUpperCase();
        const url = getCompiledUrl();
        
        const headers = {
            'Content-Type': 'application/json'
        };
        
        const authHeader = authHeaderInput.value.trim();
        if (authHeader) headers['Authorization'] = authHeader;
        
        const opts = { method, headers };
        
        if (['POST', 'PUT', 'PATCH'].includes(method)) {
            const bodyVal = bodyEditor.value.trim();
            if (bodyVal) {
                try {
                    // Just to check if it's valid JSON before sending
                    JSON.parse(bodyVal);
                    opts.body = bodyVal;
                } catch (e) {
                    showToast('Invalid JSON in body', true);
                    return;
                }
            }
        }
        
        responseViewer.textContent = 'Executing...';
        responseMeta.classList.add('hidden');
        
        const start = performance.now();
        try {
            const res = await fetch(url, opts);
            const end = performance.now();
            
            resTime.textContent = `${Math.round(end - start)}ms`;
            resStatus.textContent = `${res.status} ${res.statusText}`;
            resStatus.className = `status-badge status-${Math.floor(res.status / 100) * 100}`;
            responseMeta.classList.remove('hidden');
            
            const contentType = res.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                const data = await res.json();
                responseViewer.textContent = JSON.stringify(data, null, 2);
            } else {
                responseViewer.textContent = await res.text();
            }
        } catch (e) {
            responseViewer.textContent = `Error: ${e.message}`;
            resStatus.textContent = 'Network Error';
            resStatus.className = `status-badge status-500`;
            responseMeta.classList.remove('hidden');
        }
    });

    // --- Snippets ---
    function updateSnippets() {
        if (!currentEndpoint) return;
        const method = currentEndpoint.method.toUpperCase();
        const url = 'http://localhost:8000' + getCompiledUrl();
        const lang = snippetLang.value;
        const auth = authHeaderInput.value.trim();
        const body = (['POST', 'PUT', 'PATCH'].includes(method)) ? bodyEditor.value.trim() : '';

        let code = '';

        if (lang === 'curl') {
            code = `curl -X '${method}' \\\n  '${url}' \\\n  -H 'accept: application/json'`;
            if (auth) code += ` \\\n  -H 'Authorization: ${auth}'`;
            if (body) {
                code += ` \\\n  -H 'Content-Type: application/json' \\\n  -d '${body.replace(/'/g, "'\\''")}'`;
            }
        } 
        else if (lang === 'python') {
            code = `import requests\n\nurl = '${url}'\nheaders = {\n  'accept': 'application/json'`;
            if (auth) code += `,\n  'Authorization': '${auth}'`;
            if (body) {
                code += `,\n  'Content-Type': 'application/json'\n}\ndata = '''${body}'''\n\n`;
                code += `response = requests.${method.toLowerCase()}(url, headers=headers, data=data)`;
            } else {
                code += `\n}\n\nresponse = requests.${method.toLowerCase()}(url, headers=headers)`;
            }
            code += `\nprint(response.json())`;
        }
        else if (lang === 'javascript') {
            code = `fetch('${url}', {\n  method: '${method}',\n  headers: {\n    'accept': 'application/json'`;
            if (auth) code += `,\n    'Authorization': '${auth}'`;
            if (body) {
                code += `,\n    'Content-Type': 'application/json'\n  },\n  body: JSON.stringify(${body})\n})`;
            } else {
                code += `\n  }\n})`;
            }
            code += `.then(response => response.json())\n.then(data => console.log(data));`;
        }
        else if (lang === 'go') {
            code = `package main\n\nimport (\n\t"fmt"\n\t"io"\n\t"net/http"\n`;
            if (body) code += `\t"strings"\n`;
            code += `)\n\nfunc main() {\n\turl := "${url}"\n\tmethod := "${method}"\n\n`;
            if (body) {
                code += `\tpayload := strings.NewReader(\`${body}\`)\n\t`;
            } else {
                code += `\tvar payload io.Reader // nil\n\t`;
            }
            code += `req, err := http.NewRequest(method, url, payload)\n\tif err != nil {\n\t\tfmt.Println(err)\n\t\treturn\n\t}\n\n`;
            code += `\treq.Header.Add("accept", "application/json")\n`;
            if (auth) code += `\treq.Header.Add("Authorization", "${auth}")\n`;
            if (body) code += `\treq.Header.Add("Content-Type", "application/json")\n`;
            code += `\n\tres, err := http.DefaultClient.Do(req)\n\tif err != nil {\n\t\tfmt.Println(err)\n\t\treturn\n\t}\n\tdefer res.Body.Close()\n\n\tbody, _ := io.ReadAll(res.Body)\n\tfmt.Println(string(body))\n}`;
        }
        else if (lang === 'java') {
            code = `import java.net.URI;\nimport java.net.http.HttpClient;\nimport java.net.http.HttpRequest;\nimport java.net.http.HttpResponse;\n\npublic class Main {\n    public static void main(String[] args) throws Exception {\n        HttpClient client = HttpClient.newHttpClient();\n        \n        HttpRequest request = HttpRequest.newBuilder()\n            .uri(URI.create("${url}"))\n`;
            if (body) {
                code += `            .method("${method}", HttpRequest.BodyPublishers.ofString(${JSON.stringify(body)}))\n`;
            } else {
                code += `            .method("${method}", HttpRequest.BodyPublishers.noBody())\n`;
            }
            code += `            .header("accept", "application/json")\n`;
            if (auth) code += `            .header("Authorization", "${auth}")\n`;
            if (body) code += `            .header("Content-Type", "application/json")\n`;
            code += `            .build();\n            \n        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());\n        System.out.println(response.body());\n    }\n}`;
        }
        else if (lang === 'php') {
            code = `<?php\n\n$curl = curl_init();\n\ncurl_setopt_array($curl, [\n  CURLOPT_URL => "${url}",\n  CURLOPT_RETURNTRANSFER => true,\n  CURLOPT_ENCODING => "",\n  CURLOPT_MAXREDIRS => 10,\n  CURLOPT_TIMEOUT => 30,\n  CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_1_1,\n  CURLOPT_CUSTOMREQUEST => "${method}",\n`;
            if (body) {
                code += `  CURLOPT_POSTFIELDS => ${JSON.stringify(body)},\n`;
            }
            code += `  CURLOPT_HTTPHEADER => [\n    "accept: application/json",\n`;
            if (auth) code += `    "Authorization: ${auth}",\n`;
            if (body) code += `    "Content-Type: application/json",\n`;
            code += `  ],\n]);\n\n$response = curl_exec($curl);\n$err = curl_error($curl);\n\ncurl_close($curl);\n\nif ($err) {\n  echo "cURL Error #:" . $err;\n} else {\n  echo $response;\n}`;
        }
        else if (lang === 'csharp') {
            code = `using System;\nusing System.Net.Http;\nusing System.Text;\nusing System.Threading.Tasks;\n\nclass Program\n{\n    static async Task Main()\n    {\n        using var client = new HttpClient();\n        var request = new HttpRequestMessage(new HttpMethod("${method}"), "${url}");\n        request.Headers.Add("accept", "application/json");\n`;
            if (auth) code += `        request.Headers.Add("Authorization", "${auth}");\n`;
            if (body) {
                code += `        request.Content = new StringContent(${JSON.stringify(body)}, Encoding.UTF8, "application/json");\n`;
            }
            code += `        \n        var response = await client.SendAsync(request);\n        response.EnsureSuccessStatusCode();\n        string responseBody = await response.Content.ReadAsStringAsync();\n        Console.WriteLine(responseBody);\n    }\n}`;
        }

        snippetViewer.textContent = code;
    }

    snippetLang.addEventListener('change', updateSnippets);

    // --- Auth Generation ---
    document.getElementById('generateToken').addEventListener('click', async () => {
        const role = document.getElementById('authRole').value;
        try {
            const res = await fetch(`/api/v1/debug/token?role=${role}`, { method: 'POST' });
            const data = await res.json();
            activeTokenInput.value = data.token;
            authHeaderInput.value = `Bearer ${data.token}`;
            tokenResult.classList.remove('hidden');
            showToast('Token generated and applied to Headers');
            updateSnippets();
        } catch (e) {
            showToast('Failed to generate token', true);
        }
    });

    document.getElementById('copyToken').addEventListener('click', () => {
        navigator.clipboard.writeText(activeTokenInput.value);
        showToast('Token copied');
    });

    // --- Tests (from previous iteration) ---
    document.getElementById('runIntegration').addEventListener('click', () => {
        // Simple redirect or implement similar fetch as before if we want to show it in the response panel
        // Let's hijack the response panel for test output to keep UI clean
        emptyState.classList.add('hidden');
        endpointView.classList.remove('hidden');
        epName.textContent = 'Integration Tests';
        epDesc.textContent = 'Running scripts/test_routes.py';
        epMethod.textContent = 'TEST';
        epMethod.className = 'method-badge';
        responseViewer.textContent = 'Executing tests...';
        
        fetch('/api/v1/debug/run-tests', { method: 'POST' })
            .then(r => r.json())
            .then(data => {
                responseViewer.textContent = `--- STDOUT ---\n${data.stdout}\n--- STDERR ---\n${data.stderr}\nExit Code: ${data.exit_code}`;
            });
    });

    document.getElementById('runPytest').addEventListener('click', () => {
        emptyState.classList.add('hidden');
        endpointView.classList.remove('hidden');
        epName.textContent = 'Pytest Suite';
        epDesc.textContent = 'Running pytest tests/';
        epMethod.textContent = 'TEST';
        epMethod.className = 'method-badge';
        responseViewer.textContent = 'Executing pytest...';
        
        fetch('/api/v1/debug/run-pytest', { method: 'POST' })
            .then(r => r.json())
            .then(data => {
                responseViewer.textContent = `--- STDOUT ---\n${data.stdout}\n--- STDERR ---\n${data.stderr}\nExit Code: ${data.exit_code}`;
            });
    });

    // --- Toast ---
    function showToast(msg, isError = false) {
        const toast = document.getElementById('toast');
        toast.textContent = msg;
        toast.style.borderColor = isError ? 'var(--accent-red)' : 'var(--accent-blue)';
        toast.style.color = isError ? 'var(--accent-red)' : 'var(--accent-blue)';
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 3000);
    }

    init();
});
