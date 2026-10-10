import re

with open("backend/static/js/app.js", "r", encoding="utf-8") as f:
    content = f.read()

# Find the block starting with "if (document.getElementById('askBtn')) {"
start_str = "if (document.getElementById('askBtn')) {"
start_idx = content.find(start_str)

end_str = "if (document.getElementById('historyList')) {"
end_idx = content.find(end_str)

new_ask_block = """if (document.getElementById('askBtn')) {
    const askBtn = document.getElementById('askBtn');
    const questionInput = document.getElementById('questionInput');
    const chatHistory = document.getElementById('chatHistory');
    const documentSelector = document.getElementById('documentSelector');
    const selectAllDocs = document.getElementById('selectAllDocs');
    const docLoadingText = document.getElementById('docLoadingText');

    let allDocIds = [];

    async function loadDocumentsForSidebar() {
        try {
            const docs = await apiCall('documents/');
            docLoadingText.style.display = 'none';
            if (docs.length === 0) {
                documentSelector.innerHTML = '<p class="text-sm text-slate-500 p-2">No documents uploaded.</p>';
                return;
            }
            allDocIds = docs.map(d => d.id);
            documentSelector.innerHTML = docs.map(doc => `
                <label class="flex items-center space-x-2 cursor-pointer p-2 hover:bg-slate-50 dark:hover:bg-slate-700 rounded transition-colors">
                    <input type="checkbox" value="${doc.id}" class="doc-checkbox form-checkbox h-4 w-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500" checked>
                    <span class="text-sm text-slate-600 dark:text-slate-300 truncate" title="${doc.filename}">${doc.filename}</span>
                </label>
            `).join('');

            const checkboxes = document.querySelectorAll('.doc-checkbox');
            checkboxes.forEach(cb => cb.addEventListener('change', () => {
                const allChecked = Array.from(checkboxes).every(c => c.checked);
                selectAllDocs.checked = allChecked;
            }));
        } catch (e) {
            console.error(e);
            docLoadingText.innerText = 'Error loading documents.';
        }
    }

    if (selectAllDocs) {
        selectAllDocs.addEventListener('change', (e) => {
            const checkboxes = document.querySelectorAll('.doc-checkbox');
            checkboxes.forEach(cb => cb.checked = e.target.checked);
        });
    }

    loadDocumentsForSidebar();

    function appendUserMessage(text) {
        const div = document.createElement('div');
        div.className = 'flex items-start gap-4 flex-row-reverse';
        div.innerHTML = `
            <div class="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-600 flex items-center justify-center flex-shrink-0">
                <svg class="w-5 h-5 text-slate-600 dark:text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>
            </div>
            <div class="bg-blue-600 text-white rounded-2xl rounded-tr-sm px-5 py-3 max-w-[85%] shadow-sm">
                <p class="whitespace-pre-wrap">${text}</p>
            </div>
        `;
        chatHistory.appendChild(div);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function appendAIMessage(id) {
        const div = document.createElement('div');
        div.id = id;
        div.className = 'flex items-start gap-4';
        div.innerHTML = `
            <div class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
            </div>
            <div class="bg-slate-100 dark:bg-slate-700 rounded-2xl rounded-tl-sm px-5 py-3 max-w-[95%] min-w-[50%] shadow-sm overflow-x-auto">
                <div class="typing-indicator flex space-x-1 p-2">
                    <div class="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
                    <div class="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                    <div class="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                </div>
                <div class="message-content markdown-body hidden text-slate-800 dark:text-slate-200"></div>
                <div class="sources-container mt-4 pt-4 border-t border-slate-200 dark:border-slate-600 hidden">
                    <p class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase mb-2">Sources</p>
                    <div class="sources-grid grid grid-cols-1 md:grid-cols-2 gap-2"></div>
                </div>
            </div>
        `;
        chatHistory.appendChild(div);
        chatHistory.scrollTop = chatHistory.scrollHeight;
        return div;
    }

    function updateAIMessage(div, result) {
        const typing = div.querySelector('.typing-indicator');
        const content = div.querySelector('.message-content');
        const sourcesCont = div.querySelector('.sources-container');
        const sourcesGrid = div.querySelector('.sources-grid');

        typing.classList.add('hidden');
        content.classList.remove('hidden');

        let rawAnswer = result.answer || "No response generated.";
        
        // Use marked.js for markdown formatting
        if (typeof marked !== 'undefined') {
            content.innerHTML = marked.parse(rawAnswer);
        } else {
            content.innerText = rawAnswer;
        }

        if (result.sources && result.sources.length > 0) {
            sourcesCont.classList.remove('hidden');
            result.sources.forEach(src => {
                const sDiv = document.createElement('div');
                sDiv.className = 'text-xs p-2 bg-white dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-600 flex items-center gap-2 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors';
                sDiv.onclick = () => { window.open('/media/pages/' + src.page_image, '_blank'); };
                sDiv.innerHTML = `
                    <span class="font-bold text-blue-600 dark:text-blue-400 truncate w-24" title="${src.document_name}">${src.document_name}</span>
                    <span class="text-slate-500 line-clamp-1 flex-1">${src.snippet}</span>
                `;
                sourcesGrid.appendChild(sDiv);
            });
        }
        
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    questionInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            askBtn.click();
        }
    });

    askBtn.onclick = async () => {
        const question = questionInput.value.trim();
        if (!question) return;
        
        // Get selected documents
        const checkboxes = document.querySelectorAll('.doc-checkbox:checked');
        const document_ids = Array.from(checkboxes).map(c => c.value);

        questionInput.value = '';
        askBtn.disabled = true;

        appendUserMessage(question);
        const msgId = 'msg-' + Date.now();
        const aiBubble = appendAIMessage(msgId);

        try {
            const result = await apiCall('query/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question, document_ids }),
            });
            updateAIMessage(aiBubble, result);
        } catch (e) {
            updateAIMessage(aiBubble, { answer: `**Error:** ${e.message}` });
        } finally {
            askBtn.disabled = false;
            questionInput.focus();
        }
    };
}
"""

new_content = content[:start_idx] + new_ask_block + "\n" + content[end_idx:]
with open("backend/static/js/app.js", "w", encoding="utf-8") as f:
    f.write(new_content)
