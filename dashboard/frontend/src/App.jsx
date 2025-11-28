import React, { useState, useEffect, useCallback } from 'react';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import { Activity, Terminal, Brain, BarChart3, Wifi, WifiOff } from 'lucide-react';
import AgentStatus from './components/AgentStatus';
import LiveLogs from './components/LiveLogs';
import BrainVoting from './components/BrainVoting';
import MarketStatus from './components/MarketStatus';

const WS_URL = 'ws://localhost:8000/ws';

function App() {
  const [socketUrl] = useState(WS_URL);
  const { lastMessage, readyState } = useWebSocket(socketUrl, {
    shouldReconnect: (closeEvent) => true,
  });

  const [logs, setLogs] = useState([]);
  const [marketStatus, setMarketStatus] = useState({ sessions: [], liquidity: 'UNKNOWN' });
  const [votingData, setVotingData] = useState({});
  const [agentStatus, setAgentStatus] = useState({});

  useEffect(() => {
    if (lastMessage !== null) {
      try {
        const payload = JSON.parse(lastMessage.data);
        const { channel, data } = payload;

        if (channel === 'logs') {
          // Parse log string if it's JSON, otherwise keep as string
          // Assuming backend sends raw log strings or JSON objects
          setLogs((prev) => [data, ...prev].slice(0, 100)); // Keep last 100 logs
        } else if (channel === 'market_status') {
          setMarketStatus(typeof data === 'string' ? JSON.parse(data) : data);
        } else if (channel === 'brain_status') {
          // Update voting data
          // Expected data: { pair: "EUR/USD", buy: 5.0, sell: 2.0, decision: "BUY" }
          const status = typeof data === 'string' ? JSON.parse(data) : data;
          setVotingData((prev) => ({ ...prev, [status.pair]: status }));
        } else if (channel.startsWith('signals:')) {
          // Update agent status based on signal activity
          // data: { agent: "sentiment_agent", ... }
          const signal = typeof data === 'string' ? JSON.parse(data) : data;
          if (signal.agent) {
            setAgentStatus((prev) => ({
              ...prev,
              [signal.agent]: { status: 'active', last_seen: Date.now() }
            }));
          }
        }
      } catch (e) {
        console.error("Error parsing WS message:", e);
      }
    }
  }, [lastMessage]);

  const connectionStatus = {
    [ReadyState.CONNECTING]: 'Connecting',
    [ReadyState.OPEN]: 'Open',
    [ReadyState.CLOSING]: 'Closing',
    [ReadyState.CLOSED]: 'Closed',
    [ReadyState.UNINSTANTIATED]: 'Uninstantiated',
  }[readyState];

  return (
    <div className="min-h-screen bg-background text-foreground font-sans p-6 dark">
      <header className="flex justify-between items-center mb-8">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary rounded-lg">
            <Activity className="w-6 h-6 text-primary-foreground" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight">J.A.R.V.I.S. Command Center</h1>
        </div>
        <div className="flex items-center gap-4">
          <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${readyState === ReadyState.OPEN ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'}`}>
            {readyState === ReadyState.OPEN ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
            {connectionStatus}
          </div>
        </div>
      </header>

      <div className="grid grid-cols-12 gap-6">
        {/* Left Column: Market & Agents */}
        <div className="col-span-12 lg:col-span-3 space-y-6">
          <MarketStatus data={marketStatus} />
          <AgentStatus agents={agentStatus} />
        </div>

        {/* Middle Column: Brain & Charts */}
        <div className="col-span-12 lg:col-span-6 space-y-6">
          <BrainVoting data={votingData} />
          {/* Placeholder for Chart */}
          <div className="bg-card border border-border rounded-xl p-6 h-[400px] flex items-center justify-center text-muted-foreground">
            <BarChart3 className="w-12 h-12 mb-2 opacity-20" />
            <span className="block">TradingView Chart Integration (Coming Soon)</span>
          </div>
        </div>

        {/* Right Column: Logs */}
        <div className="col-span-12 lg:col-span-3">
          <LiveLogs logs={logs} />
        </div>
      </div>
    </div>
  );
}

export default App;
