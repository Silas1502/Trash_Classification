"use client";

import { useEffect, useId, useLayoutEffect, useRef, useState } from "react";
import { CircleCheck, Hand, Images, LoaderCircle } from "lucide-react";
import HistoryDailyTable from "@/components/history/HistoryDailyTable";
import { Button, Skeleton } from "@/components/ui/Primitives";
import { errorMessage } from "@/services/api";
import { getHistoryTrends } from "@/services/historyService";
import { modelWasteTypes, type HistoryTrendPeriod, type HistoryTrendPoint, type HistoryTrendsResponse } from "@/types";

const periods = [
  { value: "today", label: "Hôm nay" },
  { value: "week", label: "1 tuần" },
  { value: "month", label: "1 tháng" },
  { value: "quarter", label: "3 tháng" },
] as const;
const decisionSeries = [
  { field: "automatic", label: "Tự động", tone: "auto" },
  { field: "needs_review", label: "Cần kiểm tra", tone: "review" },
] as const;
const countFormat = new Intl.NumberFormat("vi-VN");
const timeFormat = new Intl.DateTimeFormat("vi-VN", {
  timeZone: "Asia/Ho_Chi_Minh", hour: "2-digit", minute: "2-digit", hourCycle: "h23",
});

function showDate(date: string) {
  const [, month, day] = date.split("-");
  return day + "/" + month;
}

function interval(point: HistoryTrendPoint) {
  if (point.start_at && point.end_at) return timeFormat.format(new Date(point.start_at)) + " – " +
    timeFormat.format(new Date(point.end_at));
  return showDate(point.start_date) + (point.start_date === point.end_date ? "" : " – " + showDate(point.end_date));
}

function axisLabel(point: HistoryTrendPoint) {
  return point.start_at ? timeFormat.format(new Date(point.start_at)).slice(0, 2) + "h" : showDate(point.start_date);
}

function share(value: number, total: number) {
  return new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 1 }).format(total > 0 ? value * 100 / total : 0) + "%";
}

type DecisionCounts = Pick<HistoryTrendPoint, "automatic" | "needs_review">;
type TooltipEntry = { label: string; count: number; total: number; breakdown?: DecisionCounts };

function useChartTooltip(total: number) {
  const id = useId();
  const [value, setValue] = useState<TooltipEntry & { x: number; y: number }>();

  function show(entry: TooltipEntry, x: number, y: number) {
    const height = entry.breakdown ? 145 : 104;
    setValue({
      ...entry,
      x: Math.max(8, Math.min(x + 12, window.innerWidth - 242)),
      y: y >= height + 8 ? y - height : Math.max(8, Math.min(y + 14, window.innerHeight - height)),
    });
  }

  function hide() { setValue(undefined); }

  function target(label: string, count: number, denominator = total, breakdown?: DecisionCounts) {
    const entry: TooltipEntry = { label, count, total: denominator, breakdown };
    function showAtElement(element: Element) {
      const rect = element.getBoundingClientRect();
      show(entry, rect.x + rect.width / 2, rect.y + rect.height / 2);
    }

    return {
      tabIndex: 0,
      "aria-label": breakdown
        ? `${label}, Tự động ${countFormat.format(breakdown.automatic)} ảnh, Cần kiểm tra ${countFormat.format(breakdown.needs_review)} ảnh`
        : `${label}, ${countFormat.format(count)} ảnh, ${share(count, denominator)} trên tổng ${countFormat.format(denominator)} ảnh trong khoảng`,
      "aria-describedby": value?.label === label ? id : undefined,
      onPointerEnter: (event: React.PointerEvent<Element>) => show(entry, event.clientX, event.clientY),
      onPointerMove: (event: React.PointerEvent<Element>) => show(entry, event.clientX, event.clientY),
      onPointerLeave: hide,
      onFocus: (event: React.FocusEvent<Element>) => showAtElement(event.currentTarget),
      onBlur: hide,
      onClick: (event: React.MouseEvent<Element>) => showAtElement(event.currentTarget),
      onKeyDown: (event: React.KeyboardEvent<Element>) => { if (event.key === "Escape") hide(); },
    };
  }

  const tooltip = value && <div id={id} className="chart-tooltip" role="tooltip" style={{ left: value.x, top: value.y }}>
    <strong>{value.label}</strong>
    {value.breakdown ? <>
      {decisionSeries.map(({ field, label, tone }) => {
        const count = value.breakdown?.[field] ?? 0;
        return <span key={field} className={`chart-tooltip-${tone}`}>
          {label} <b>{countFormat.format(count)} ảnh</b>{value.total > 0 && <> · {share(count, value.total)}</>}
        </span>;
      })}
      <small>Tổng hai luồng tại mốc này {countFormat.format(value.count)} ảnh</small>
    </> : <>
      <span><b>{countFormat.format(value.count)} ảnh</b>{value.total > 0 && <> · {share(value.count, value.total)}</>}</span>
      <small>trên tổng {countFormat.format(value.total)} ảnh trong khoảng</small>
    </>}
  </div>;
  return { target, tooltip, hide };
}

type TimeChartProps = { points: HistoryTrendPoint[]; interaction: ReturnType<typeof useChartTooltip> };

function TimeChart({ points, interaction }: TimeChartProps) {
  const { target } = interaction;
  const title = "Số ảnh đã phân loại theo thời gian";
  const width = 700;
  const height = 280;
  const left = 54;
  const top = 30;
  const bottom = 228;
  const slot = (width - left - 20) / Math.max(1, points.length);
  const observed = points.map((point, index) => ({ point, index })).filter(({ point }) => !point.is_future);
  const peak = Math.max(0, ...observed.map(({ point }) => point.total));
  const step = Math.max(1, Math.ceil(peak / 4));
  const divisions = Math.max(1, Math.ceil(peak / step));
  const y = (value: number) => bottom - (bottom - top) * value / (divisions * step);
  const x = (index: number) => left + (index + 0.5) * slot;
  const labelStep = Math.ceil(points.length / 7);
  const totalLine = observed.map(({ point, index }) => `${x(index)},${y(point.total)}`).join(" ");

  return <figure className="history-chart">
    <figcaption>{title}</figcaption>
    <div className="chart-line-spacer" aria-hidden />
    <div className="chart-scroll">
      <svg className="analytics-chart-svg" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={title}>
        {Array.from({ length: divisions + 1 }, (_, index) => {
          const value = index * step;
          return <g key={value}>
            <line x1={left} x2={width - 16} y1={y(value)} y2={y(value)} className="chart-gridline" />
            <text x={left - 7} y={y(value)} dy=".32em" textAnchor="end">{countFormat.format(value)}</text>
          </g>;
        })}
        {observed.length > 0 && <>
          <polygon className="chart-area" points={
            `${x(observed[0].index)},${bottom} ` + totalLine +
            ` ${x(observed[observed.length - 1].index)},${bottom}`
          } />
          <polyline className="chart-line" points={totalLine} />
        </>}
        {points.map((point, index) => <g key={point.start_at ?? point.start_date}>
          {!point.is_future && <g className="chart-value" {...target(interval(point) + " · Tổng số ảnh", point.total)}>
            <circle className="chart-point" cx={x(index)} cy={y(point.total)} r={points.length > 13 ? 3 : 4} />
            {points.length <= 13 && <text className="chart-value-label" x={x(index)} y={y(point.total) - 12} textAnchor="middle">{point.total}</text>}
            <rect x={x(index) - slot / 2} y={top - 14} width={slot} height={bottom - top + 25} fill="transparent" />
          </g>}
          {(index % labelStep === 0 || index === points.length - 1) &&
            <text x={x(index)} y={bottom + 21} textAnchor="middle">{axisLabel(point)}</text>}
        </g>)}
        <text className="chart-axis-label" x={width - 20} y={height - 5} textAnchor="end">Thời gian</text>
      </svg>
    </div>
  </figure>;
}

const stackedSlotWidth = 46;

function StackedDecisionChart({ points, interaction }: TimeChartProps) {
  const title = "Tự động và cần kiểm tra theo thời gian";
  const titleId = useId();
  const scrollRef = useRef<HTMLDivElement>(null);
  const [overflowing, setOverflowing] = useState(false);
  const firstFuture = points.findIndex(point => point.is_future);
  const observedCount = firstFuture === -1 ? points.length : firstFuture;
  const peak = Math.max(0, ...points.filter(point => !point.is_future).map(point => point.automatic + point.needs_review));
  const step = Math.max(1, Math.ceil(peak / 4));
  const divisions = Math.max(1, Math.ceil(peak / step));
  const maximum = divisions * step;
  const ticks = Array.from({ length: divisions + 1 }, (_, index) => index * step);
  const height = (count: number) => `${count * 100 / maximum}%`;

  useLayoutEffect(() => {
    const viewport = scrollRef.current;
    if (!viewport || points.length === 0) return;

    const mostRecent = viewport.scrollWidth * observedCount / points.length;
    viewport.scrollLeft = Math.max(0, mostRecent - viewport.clientWidth);

    const checkOverflow = () => setOverflowing(viewport.scrollWidth > viewport.clientWidth);
    checkOverflow();
    const observer = new ResizeObserver(checkOverflow);
    observer.observe(viewport);
    return () => observer.disconnect();
  }, [points, observedCount]);

  return <figure className="history-chart stacked-decision-chart" aria-labelledby={titleId}>
    <figcaption id={titleId}>{title}</figcaption>
    <div className="stacked-chart-legend">
      {decisionSeries.map(({ field, label, tone }) => <span key={field}>
        <i className={`stacked-fill-${tone}`} aria-hidden />{label}
      </span>)}
      {firstFuture !== -1 && <span><i className="stacked-future-mark" aria-hidden />Chưa đến</span>}
    </div>
    <div className="stacked-chart-layout">
      <div className="stacked-chart-axis" aria-hidden>
        <span className="stacked-axis-width">{countFormat.format(maximum)}</span>
        {ticks.map(value => <span className="stacked-axis-tick" key={value} style={{ bottom: height(value) }}>
          {countFormat.format(value)}
        </span>)}
      </div>
      <div className="stacked-chart-scroll" ref={scrollRef} onScroll={interaction.hide}
        role="group" aria-label="Số ảnh theo từng mốc thời gian" tabIndex={overflowing ? 0 : undefined}>
        <div className="stacked-chart-track" style={{ minWidth: points.length * stackedSlotWidth }}>
          <div className="stacked-chart-grid" aria-hidden>
            {ticks.map(value => <i key={value} style={{ bottom: height(value) }} />)}
          </div>
          {points.map(point => {
            const count = point.automatic + point.needs_review;
            return <div className="stacked-chart-bucket" key={point.start_at ?? point.start_date}>
              <div className="stacked-chart-slot">
                {point.is_future
                  ? <span className="stacked-future-mark"><span className="sr-only">Chưa đến</span></span>
                  : <button type="button" className="stacked-chart-target"
                      {...interaction.target(interval(point), count, count, point)}>
                      {count > 0 ? <>
                        <span className="stacked-chart-column" style={{ height: height(count) }} aria-hidden>
                          {decisionSeries.map(({ field, tone }) => point[field] > 0 &&
                            <span key={field} className={`stacked-fill-${tone}`} style={{ flexGrow: point[field] }} />)}
                        </span>
                        <span className="stacked-chart-total" style={{ bottom: height(count) }} aria-hidden>
                          {countFormat.format(count)}
                        </span>
                      </> : <span className="stacked-zero-mark" aria-hidden />}
                    </button>}
              </div>
              <span className="stacked-chart-time" aria-hidden>{axisLabel(point)}</span>
            </div>;
          })}
        </div>
      </div>
    </div>
    <div className="stacked-chart-footer">
      {overflowing && <span>Cuộn ngang để xem thêm</span>}
      <span>Thời gian</span>
    </div>
  </figure>;
}

function WasteChart({ counts, interaction }: {
  counts: HistoryTrendsResponse["by_waste_type"]; interaction: ReturnType<typeof useChartTooltip>;
}) {
  const { target } = interaction;
  const colors = { "Nhựa": "#2464bd", "Giấy": "#d69a33", "Kim loại": "#657b99", "Thủy tinh": "#368964" };
  const total = modelWasteTypes.reduce((sum, label) => sum + counts[label], 0);
  const radius = 96;
  const circumference = 2 * Math.PI * radius;
  let offset = 0;
  const types = modelWasteTypes.map(label => {
    const count = counts[label];
    const fraction = total > 0 ? count / total : 0;
    const angle = (offset + fraction / 2) * 2 * Math.PI - Math.PI / 2;
    const segment = { label, count, fraction, angle, offset, color: colors[label] };
    offset += fraction;
    return segment;
  });
  const labels = types.filter(type => type.count > 0).map(type => ({
    ...type, x: Math.cos(type.angle) >= 0 ? 338 : 62, y: 140 + Math.sin(type.angle) * 121,
  }));
  for (const side of [62, 338]) {
    const group = labels.filter(label => label.x === side).sort((a, b) => a.y - b.y);
    let previous = -10;
    for (const label of group) {
      label.y = Math.max(18, label.y, previous + 23);
      previous = label.y;
    }
    const overflow = Math.max(0, previous - 262);
    for (const label of group) label.y -= overflow;
  }
  return <figure className="history-chart waste-chart">
    <figcaption>Số ảnh theo loại rác</figcaption>
    <div className="donut-layout">
      <svg className="donut-chart-svg" viewBox="0 0 400 280" role="img" aria-label="Số ảnh theo loại rác">
        <circle className="donut-track" cx={200} cy={140} r={radius} />
        {types.filter(type => type.count > 0).map(type => <g className="chart-value" key={type.label}
          {...target(type.label, type.count, total)}>
          <circle className="donut-segment" cx={200} cy={140} r={radius}
            stroke={type.color} strokeDasharray={`${type.fraction * circumference} ${circumference}`}
            strokeDashoffset={-type.offset * circumference} transform="rotate(-90 200 140)" />
        </g>)}
        <g className="chart-value" {...target("Tổng số ảnh của 4 loại rác", total, total)}>
          <text className="donut-total" x={200} y={137} textAnchor="middle">{countFormat.format(total)}</text>
          <text className="donut-total-label" x={200} y={160} textAnchor="middle">ảnh · 4 loại rác</text>
        </g>
        {labels.map(type => <g className="chart-value" key={type.label} {...target(type.label, type.count, total)}>
          <polyline className="donut-label-line" points={
            `${200 + Math.cos(type.angle) * 121},${140 + Math.sin(type.angle) * 121} ${type.x + (type.x < 200 ? 7 : -7)},${type.y}`
          } />
          <text className="donut-percentage" x={type.x} y={type.y} dy=".32em"
            textAnchor={type.x < 200 ? "end" : "start"}>{share(type.count, total)}</text>
        </g>)}
      </svg>
      <dl className="donut-legend">
        {types.map(type => <div key={type.label}>
          <dt><i style={{ background: type.color }} aria-hidden />{type.label}</dt>
          <dd>{countFormat.format(type.count)} ảnh</dd>
        </div>)}
      </dl>
    </div>
  </figure>;
}

function WasteCharacteristics() {
  const descriptions = [
    { label: "Nhựa", text: "Chai, hộp, túi và bao bì. Bề mặt thường trơn hoặc nhăn, có thể trong hoặc có màu." },
    { label: "Giấy", text: "Tờ giấy, bìa và hộp carton. Thường có nếp gấp, mép xé hoặc thớ giấy." },
    { label: "Kim loại", text: "Lon và hộp kim loại. Bề mặt thường phản sáng, có thể có vết móp hoặc nếp gấp." },
    { label: "Thủy tinh", text: "Chai, lọ và cốc. Thường trong hoặc bán trong, có vùng phản sáng ở mép và bề mặt." },
  ];
  return <section className="history-chart waste-characteristics" aria-labelledby="waste-characteristics-title">
    <h3 id="waste-characteristics-title">Đặc điểm các loại rác</h3>
    <dl>{descriptions.map(({ label, text }) => <div key={label}><dt>{label}</dt><dd>{text}</dd></div>)}</dl>
  </section>;
}

function PredictionSummary({ data }: { data: HistoryTrendsResponse }) {
  const cards = [
    { label: "Số lượng ảnh đã phân loại", value: data.points.reduce((sum, point) => sum + point.total, 0), tone: "blue", icon: Images },
    { label: "Số lượng ảnh phân loại tự động", value: data.points.reduce((sum, point) => sum + point.automatic, 0), tone: "green", icon: CircleCheck },
    { label: "Số lượng ảnh phân loại thủ công", value: data.points.reduce((sum, point) => sum + point.needs_review, 0), tone: "amber", icon: Hand },
  ];
  return <dl className="chart-summary" aria-label="Tổng quan phân loại">
    {cards.map(({ label, value, tone, icon: Icon }) => <div className={"chart-summary-card summary-" + tone} key={label}>
      <dt><Icon aria-hidden />{label}</dt>
      <dd>{countFormat.format(value)}</dd>
    </div>)}
  </dl>;
}

export default function HistoryCharts() {
  const [period, setPeriod] = useState<HistoryTrendPeriod>("today");
  const [data, setData] = useState<HistoryTrendsResponse>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>();
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(undefined);
    getHistoryTrends(period, controller.signal)
      .then(value => { if (!controller.signal.aborted) setData(value); })
      .catch(error => { if (!controller.signal.aborted) setError(errorMessage(error, "Không thể tải biểu đồ lịch sử.")); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [period, retry]);

  const points = data?.points;
  const total = points?.reduce((sum, point) => sum + point.total, 0) ?? 0;
  const interaction = useChartTooltip(total);
  return <div className="history-charts" aria-busy={loading}>
    <div className="chart-toolbar">
      <div className="chart-periods" role="group" aria-label="Khoảng thời gian biểu đồ">
        {periods.map(({ value, label }) => <Button key={value}
          variant={value === period ? "primary" : "outline"} aria-pressed={value === period}
          onClick={() => { interaction.hide(); setPeriod(value); }}>
          {label}
        </Button>)}
      </div>
      {loading && <span className="chart-loading" role="status"><LoaderCircle className="spin" aria-hidden />Đang cập nhật…</span>}
    </div>
    {error && <div className="chart-error">
      <p role="alert">{error}</p><Button variant="outline" onClick={() => setRetry(value => value + 1)}>Thử tải lại biểu đồ</Button>
    </div>}
    {loading && !data && <Skeleton rows={3} />}
    {data && <>
      <PredictionSummary data={data} />
      <div className="trend-charts" aria-busy={loading}>
        <TimeChart key={data.points[0]?.start_date + "-total"} points={data.points} interaction={interaction} />
        <StackedDecisionChart points={data.points} interaction={interaction} />
        <WasteChart key={data.points[0]?.start_date + "-waste"} counts={data.by_waste_type} interaction={interaction} />
        <WasteCharacteristics />
      </div>
      {total === 0 && <p className="chart-empty" role="status">Không có ảnh trong khoảng đã chọn.</p>}
    </>}
    <HistoryDailyTable />
    {interaction.tooltip}
  </div>;
}
