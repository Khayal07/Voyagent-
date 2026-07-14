import { motion, useReducedMotion } from "motion/react";
import { AGENT_NAMES, type AgentName, type AgentStatus } from "../../hooks/useAgentStatuses";
import AgentNode from "./AgentNode";

interface Props {
  statuses: Record<AgentName, AgentStatus>;
}

export default function AgentNodeBar({ statuses }: Props) {
  const reduced = useReducedMotion();
  return (
    <motion.div
      className="hud-glass flex items-start justify-around px-3 py-3"
      initial={reduced ? false : "hidden"}
      animate="show"
      variants={{ show: { transition: { staggerChildren: 0.06 } } }}
    >
      {AGENT_NAMES.map((agent) => (
        <motion.div
          key={agent}
          variants={{
            hidden: { opacity: 0, scale: 0.6 },
            show: {
              opacity: 1,
              scale: 1,
              transition: { type: "spring", stiffness: 380, damping: 24 },
            },
          }}
        >
          <AgentNode agent={agent} status={statuses[agent]} />
        </motion.div>
      ))}
    </motion.div>
  );
}
