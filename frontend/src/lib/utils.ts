export function cn(...classes: (string | false | undefined | null)[]) {
  return classes.filter(Boolean).join(" ");
}

export function percent(value: number) {
  return value.toFixed(1) + "%";
}

const durationFormatter = new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 2 });

export function formatDuration(milliseconds: number) {
  return milliseconds >= 1000
    ? durationFormatter.format(milliseconds / 1000) + " giây"
    : durationFormatter.format(milliseconds) + " ms";
}

const dateFormatter = new Intl.DateTimeFormat("vi-VN", {
  timeZone: "Asia/Ho_Chi_Minh",
  year: "numeric", month: "2-digit", day: "2-digit",
  hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23",
});

export function formatDate(value: string) {
  const parts = Object.fromEntries(dateFormatter.formatToParts(new Date(value)).map(({ type, value }) => [type, value]));
  return [parts.day, parts.month, parts.year].join("/") + " " + [parts.hour, parts.minute, parts.second].join(":");
}

export function formatSize(bytes: number) {
  return bytes >= 1024 ** 2 ? (bytes / 1024 ** 2).toFixed(2) + " MB" : Math.ceil(bytes / 1024) + " KB";
}

export function downloadBlob(data: Blob, fileName: string) {
  const url = URL.createObjectURL(data);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  document.body.append(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export const imageAccept = "image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp";
export const maxImageBytes = 8 * 1024 ** 2;

export function isImage(file: File) {
  return /^(image\/jpeg|image\/png|image\/webp)$/i.test(file.type) ||
    (!file.type && /\.(jpe?g|png|webp)$/i.test(file.name));
}

export function uploadFile(file: File) {
  if (file.type) return file;
  const type = /\.png$/i.test(file.name) ? "image/png" : /\.webp$/i.test(file.name) ? "image/webp" : "image/jpeg";
  return new File([file], file.name, { type, lastModified: file.lastModified });
}
