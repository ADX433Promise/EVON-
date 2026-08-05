const fileInput = document.getElementById('fileInput');
const dropzone = document.getElementById('dropzone');
const createLinkBtn = document.getElementById('createLinkBtn');
const limitInput = document.getElementById('limitInput');
const progressBar = document.getElementById('progressBar');
const message = document.getElementById('message');
const linkBox = document.getElementById('linkBox');
const shareLink = document.getElementById('shareLink');

let selectedFile = null;
let demoUrl = null;

const updateMessage = (text) => {
  message.textContent = text;
};

const setProgress = (value) => {
  progressBar.style.width = `${value}%`;
};

const handleFileSelection = (file) => {
  if (!file) return;
  selectedFile = file;
  updateMessage(`تم اختيار الملف: ${file.name}`);
};

fileInput.addEventListener('change', (event) => {
  handleFileSelection(event.target.files?.[0]);
});

dropzone.addEventListener('dragover', (event) => {
  event.preventDefault();
  dropzone.classList.add('active');
});

dropzone.addEventListener('dragleave', () => {
  dropzone.classList.remove('active');
});

dropzone.addEventListener('drop', (event) => {
  event.preventDefault();
  dropzone.classList.remove('active');
  handleFileSelection(event.dataTransfer.files?.[0]);
});

createLinkBtn.addEventListener('click', () => {
  if (!selectedFile) {
    updateMessage('يرجى اختيار ملف أولًا');
    return;
  }

  createLinkBtn.disabled = true;
  createLinkBtn.textContent = 'جارٍ الإنشاء...';
  setProgress(20);
  updateMessage('يتم إنشاء رابط تنزيل تجريبي...');

  if (demoUrl) {
    URL.revokeObjectURL(demoUrl);
  }

  demoUrl = URL.createObjectURL(selectedFile);
  shareLink.href = demoUrl;
  shareLink.download = selectedFile.name;
  shareLink.textContent = `${selectedFile.name} (تنزيل)`;
  linkBox.classList.remove('hidden');

  const limit = Number(limitInput.value || 1);
  setProgress(100);
  updateMessage(`تم إنشاء رابط تجريبي للملف. الحد الأقصى للفتح: ${limit}. هذا الإصدار على GitHub Pages لا يدعم رفعًا حقيقيًا على الخادم.`);

  createLinkBtn.disabled = false;
  createLinkBtn.textContent = 'إنشاء الرابط';
  setTimeout(() => setProgress(0), 800);
});
