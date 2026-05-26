function toggleValue(values: string[], value: string, max?: number) {
  if (values.includes(value)) return values.filter((item) => item !== value);
  if (max && values.length >= max) return values;
  return [...values, value];
}

export function ChoiceGroup({
  options,
  values,
  onChange,
  max
}: {
  options: string[];
  values: string[];
  onChange: (next: string[]) => void;
  max?: number;
}) {
  return (
    <div className="choice-grid">
      {options.map((option) => (
        <label className="choice" key={option}>
          <input checked={values.includes(option)} onChange={() => onChange(toggleValue(values, option, max))} type="checkbox" />
          <span>{option}</span>
        </label>
      ))}
    </div>
  );
}

export function RadioGroup({ options, value, onChange }: { options: string[]; value: string; onChange: (next: string) => void }) {
  return (
    <div className="choice-grid">
      {options.map((option) => (
        <label className="choice" key={option}>
          <input checked={value === option} onChange={() => onChange(option)} type="radio" />
          <span>{option}</span>
        </label>
      ))}
    </div>
  );
}

export function ScoreRows({
  rows,
  values,
  onChange
}: {
  rows: Array<[string, string]>;
  values: Record<string, number>;
  onChange: (key: string, value: number) => void;
}) {
  return (
    <div>
      {rows.map(([key, label]) => (
        <div className="score-row" key={key}>
          <div>{label}</div>
          <div className="score-options">
            {[1, 2, 3, 4, 5].map((score) => (
              <label key={score}>
                <input checked={values[key] === score} onChange={() => onChange(key, score)} type="radio" />
                {score}
              </label>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
