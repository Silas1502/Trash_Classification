async function readEntry(entry: FileSystemEntry): Promise<File[]> {
  if (entry.isFile) return new Promise((resolve, reject) => {
    (entry as FileSystemFileEntry).file(file => resolve([file]), reject);
  });
  if (!entry.isDirectory) return [];
  const reader = (entry as FileSystemDirectoryEntry).createReader();
  const files: File[] = [];
  for (;;) {
    const entries = await new Promise<FileSystemEntry[]>((resolve, reject) => reader.readEntries(resolve, reject));
    if (!entries.length) return files;
    for (const child of entries) files.push(...await readEntry(child));
  }
}

export function readDroppedFiles(transfer: DataTransfer): Promise<File[]> {
  const files = Array.from(transfer.files);
  const entries = Array.from(transfer.items, item => item.webkitGetAsEntry?.()).filter(entry => entry != null);
  if (!entries.some(entry => entry.isDirectory)) return Promise.resolve(files);
  return Promise.all(entries.map(readEntry)).then(groups => groups.flat());
}
