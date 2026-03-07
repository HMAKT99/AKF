import { Composition } from "remotion";
import { AKFDemo } from "./AKFDemo";
import "./index.css";

export const Root: React.FC = () => {
  return (
    <Composition
      id="AKFDemo"
      component={AKFDemo}
      durationInFrames={1800}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
