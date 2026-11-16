import { uploadFile } from "@/lib/utils";
import { api } from "@/services/api";
import type { BatchResponse, PredictionResponse } from "@/types";

export async function predictSingle(file: File, signal: AbortSignal) {
  const form = new FormData();
  form.append("file", uploadFile(file));
  return (await api.post<PredictionResponse>("/predict/single", form, { signal })).data;
}

export async function predictBatch(files: readonly File[], signal: AbortSignal) {
  const form = new FormData();
  files.forEach(file => form.append("files", uploadFile(file)));
  return (await api.post<BatchResponse>("/predict/batch", form, { signal })).data;
}

export function groupUploads<T extends { file: File }>(items: readonly T[]) {
  const groups: T[][] = [];
  let group: T[] = [];
  let bytes = 0;
  for (const item of items) {
    if (group.length >= 4 || bytes + item.file.size > 32 * 1024 ** 2) {
      if (group.length) groups.push(group);
      group = [];
      bytes = 0;
    }
    group.push(item);
    bytes += item.file.size;
  }
  if (group.length) groups.push(group);
  return groups;
}
