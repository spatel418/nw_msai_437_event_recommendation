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
          <h3 className="text-sm font-semibold text-nu-purple uppercase tracking-wider mb-2">
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
                      ? "bg-nu-purple text-white border-nu-purple shadow-md"
                      : "bg-white text-gray-700 border-gray-300 hover:border-nu-purple-light hover:text-nu-purple"
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
