import { LANE_ORDER } from "../ws/stageTaxonomy";
import { useRunStore } from "../store/runStore";
import { StageLane } from "./ui/StageLane";

export function ProgressTracker() {
  const laneUpdates = useRunStore((s) => s.laneUpdates);

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
      {LANE_ORDER.map((lane) => (
        <StageLane key={lane} lane={lane} update={laneUpdates[lane]} />
      ))}
    </div>
  );
}
