interface Props {
  groups: Record<string, string[]>;
  selected: string[];
  onToggle: (label: string) => void;
}

export default function LabelSelector({ groups, selected, onToggle }: Props) {
  return (
    <div className="space-y-6">
      {Object.entries(groups).map(([groupName, labels]) => (
        <div key={groupName}>
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-2">
            {groupName}
          </h3>
          <div className="flex flex-wrap gap-2">
            {labels.map((label) => {
              const isSelected = selected.includes(label);
              return (
                <button
                  key={label}
                  onClick={() => onToggle(label)}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all border ${
                    isSelected
                      ? "bg-indigo-600 text-white border-indigo-600 shadow-md"
                      : "bg-gray-800 text-gray-300 border-gray-600 hover:border-indigo-400 hover:text-white"
                  }`}
                >
                  {label}
                </button>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
