import { useEffect, useMemo, useState } from 'react';
import { Chart, Title } from '@highcharts/react';
import { Accessibility } from '@highcharts/react/options/Accessibility';
import { BubbleSeries } from '@highcharts/react/series/Bubble';
import './app.css';
import csvRaw from './watch-history.csv?raw';

function splitCsvLine(line) {
  const values = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];

    if (char === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }

    if (char === ',' && !inQuotes) {
      values.push(current.trim());
      current = '';
      continue;
    }

    current += char;
  }

  values.push(current.trim());
  return values;
}

function parseCsv(csvText) {
  if (!csvText) {
    return [];
  }

  const lines = csvText
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean);

  if (lines.length < 2) {
    return [];
  }

  const headers = splitCsvLine(lines[0]);
  const titleIndex = headers.indexOf('video_title');
  const dateIndex = headers.indexOf('date');
  const lengthIndex = headers.indexOf('video_length');
  const categoryIndex = headers.indexOf('video_category');

  if (
    titleIndex === -1 ||
    dateIndex === -1 ||
    lengthIndex === -1 ||
    categoryIndex === -1
  ) {
    return [];
  }

  return lines
    .slice(1)
    .map((line) => {
      const cols = splitCsvLine(line);
      const title = cols[titleIndex] || '';
      const dateValue = cols[dateIndex] || '';
      const category = cols[categoryIndex] || '';
      const videoLength = Number.parseFloat(cols[lengthIndex]);
      const date = new Date(dateValue.replace(' ', 'T'));

      if (
        !title ||
        !category ||
        Number.isNaN(videoLength) ||
        videoLength <= 0 ||
        Number.isNaN(date.getTime())
      ) {
        return null;
      }

      return {
        name: title,
        value: videoLength,
        category,
        date,
        day: date.toISOString().slice(0, 10),
      };
    })
    .filter(Boolean)
    .sort((a, b) => a.date - b.date);
}

function formatWatchTime(totalSeconds) {
  const seconds = Math.round(totalSeconds);
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = seconds % 60;

  if (hours > 0) {
    return `${hours}h ${minutes}m ${remainingSeconds}s`;
  }

  if (minutes > 0) {
    return `${minutes}m ${remainingSeconds}s`;
  }

  return `${remainingSeconds}s`;
}

function App() {
  const [viewportHeight, setViewportHeight] = useState(() => {
    if (typeof window === 'undefined') {
      return 900;
    }
    return window.innerHeight;
  });

  useEffect(() => {
    if (typeof window === 'undefined') {
      return undefined;
    }

    const handleResize = () => setViewportHeight(window.innerHeight);
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  const allRows = useMemo(() => {
    if (typeof document === 'undefined') {
      return [];
    }

    const csvText = document.getElementById('csv')?.textContent || csvRaw;
    return parseCsv(csvText);
  }, []);

  const timelineDays = useMemo(() => {
    return [...new Set(allRows.map((row) => row.day))];
  }, [allRows]);

  const [selectedDayIndex, setSelectedDayIndex] = useState(null);

  const activeDayIndex =
    selectedDayIndex == null
      ? Math.max(timelineDays.length - 1, 0)
      : Math.min(selectedDayIndex, Math.max(timelineDays.length - 1, 0));

  const activeDay = timelineDays[activeDayIndex];

  const filteredRows = useMemo(() => {
    if (!activeDay) {
      return [];
    }
    return allRows.filter((row) => row.day === activeDay);
  }, [allRows, activeDay]);

  const totalWatchSeconds = useMemo(() => {
    return filteredRows.reduce((sum, row) => sum + row.value, 0);
  }, [filteredRows]);

  const chartHeight = useMemo(() => {
    return Math.max(280, Math.min(viewportHeight - 20, 700));
  }, [viewportHeight]);

  const series = useMemo(() => {
    const grouped = new Map();

    filteredRows.forEach((row) => {
      if (!grouped.has(row.category)) {
        grouped.set(row.category, []);
      }

      grouped.get(row.category).push({
        name: row.name,
        value: row.value,
        custom: {
          watchedOn: row.date.toLocaleString(),
          category: row.category,
        },
      });
    });

    return [...grouped.entries()]
      .map(([categoryName, points]) => ({
        name: categoryName,
        data: points,
      }))
      .sort((a, b) => b.data.length - a.data.length);
  }, [filteredRows]);

  const myOpts = useMemo(
    () => ({
      chart: {
        type: 'packedbubble',
        height: chartHeight,
      },
      title: {
        text: 'What I watched over time',
        align: 'left',
      },
      subtitle: {
        text: activeDay
          ? `Showing videos watched on ${activeDay}`
          : 'No valid CSV rows to display',
        align: 'left',
      },
      tooltip: {
        useHTML: true,
        formatter: function () {
          if (this.point.value === undefined) {
            let totalLength = 0;

            if (this.series && this.series.data) {
              this.series.data.forEach((childPoint) => {
                if (childPoint.options && childPoint.options.value) {
                  totalLength += childPoint.options.value;
                }
              });
            }

            return (
              `<b>Category: ${this.series.name}</b><br/>` +
              `Total watch length: ${totalLength.toFixed(1)}s`
            );
          }

          return (
            `<b>${this.point.name}</b><br/>` +
            `Length: ${this.point.value}s<br/>` +
            `Watched: ${this.point.options.custom?.watchedOn || 'Unknown'}`
          );
        },
      },
      plotOptions: {
        packedbubble: {
          minSize: '20%',
          maxSize: '100%',
          zMin: 0,
          zMax: 3000,
          layoutAlgorithm: {
            gravitationalConstant: 0.05,
            splitSeries: true,
            seriesInteraction: false,
            dragBetweenSeries: true,
            parentNodeLimit: true,
          },
          dataLabels: {
            enabled: true,
            format: '{point.name}',
            filter: {
              property: 'value',
              operator: '>',
              value: 250,
            },
            style: {
              color: 'black',
              textOutline: 'none',
              fontWeight: 'normal',
            },
          },
        },
      },
      series,
    }),
    [series, activeDay, chartHeight]
  );

  return (
    <>
      <div className="timeline-wrap">
        <label htmlFor="timeline-slider">Timeline scrubber</label>
        <input
          id="timeline-slider"
          type="range"
          min={0}
          max={Math.max(timelineDays.length - 1, 0)}
          step={1}
          value={activeDayIndex}
          onChange={(event) => setSelectedDayIndex(Number(event.target.value))}
          disabled={!timelineDays.length}
        />
        <p>
          {activeDay
            ? `Showing ${filteredRows.length} videos on ${activeDay} | Total watch time: ${formatWatchTime(totalWatchSeconds)}`
            : 'No rows were parsed from CSV'}
        </p>
        <Chart options={myOpts} />
      </div>

      <pre id="csv">{csvRaw}</pre>
    </>
  );
}

export default App
