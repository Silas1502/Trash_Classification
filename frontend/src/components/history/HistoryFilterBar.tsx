import { CalendarDays, ChevronDown, Download, LoaderCircle } from "lucide-react";
import { Button, SearchInput } from "@/components/ui/Primitives";
import { pipelineTypes, wasteTypes, type PipelineType, type WasteType } from "@/types";

export type DateRange = "" | "today" | "week" | "month";
export interface FilterValues { search: string; waste: WasteType | ""; pipeline: PipelineType | ""; range: DateRange }
export const initialFilters: FilterValues = { search: "", waste: "", pipeline: "", range: "" };

export default function HistoryFilterBar({ value, onChange, onExport, exporting }: {
  value: FilterValues; onChange: (value: FilterValues) => void; onExport: () => void; exporting: boolean;
}) {
  return <div className="panel history-filters" aria-label="Bộ lọc lịch sử">
    <SearchInput value={value.search} onChange={search => onChange({ ...value, search })} />
    <label className="input-wrap select-control">
      <select aria-label="Loại rác" value={value.waste} onChange={event => onChange({ ...value, waste: event.target.value as FilterValues["waste"] })}>
        <option value="">Loại rác: Tất cả</option>
        {wasteTypes.map(item => <option key={item} value={item}>Loại rác: {item}</option>)}
      </select><ChevronDown aria-hidden />
    </label>
    <label className="input-wrap select-control">
      <select aria-label="Luồng xử lý" value={value.pipeline} onChange={event => onChange({ ...value, pipeline: event.target.value as FilterValues["pipeline"] })}>
        <option value="">Luồng xử lý: Tất cả</option>
        {pipelineTypes.map(item => <option key={item} value={item}>Luồng xử lý: {item}</option>)}
      </select><ChevronDown aria-hidden />
    </label>
    <label className="input-wrap select-control date-control">
      <CalendarDays className="prefix-icon" aria-hidden />
      <select aria-label="Thời gian" value={value.range} onChange={event => onChange({ ...value, range: event.target.value as DateRange })}>
        <option value="">Thời gian: Tất cả</option><option value="today">Hôm nay</option>
        <option value="week">7 ngày gần đây</option><option value="month">30 ngày gần đây</option>
      </select><ChevronDown aria-hidden />
    </label>
    <Button disabled={exporting} onClick={onExport}>{exporting ? <LoaderCircle className="spin" aria-hidden /> : <Download aria-hidden />}Xuất lịch sử</Button>
  </div>;
}
