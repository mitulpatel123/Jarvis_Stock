import React from 'react';
import { Brain } from 'lucide-react';

const BrainVoting = ({ data }) => {
    const pairs = Object.keys(data);

    return (
        <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
                <Brain className="w-5 h-5 text-primary" />
                <h2 className="text-lg font-semibold">Brain Decision Engine</h2>
            </div>

            {pairs.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">No active voting sessions</div>
            ) : (
                <div className="space-y-6">
                    {pairs.map((pair) => {
                        const { buy, sell, decision, confidence } = data[pair];
                        const total = buy + sell;
                        const buyPct = total > 0 ? (buy / total) * 100 : 0;
                        const sellPct = total > 0 ? (sell / total) * 100 : 0;

                        return (
                            <div key={pair} className="space-y-2">
                                <div className="flex justify-between items-center">
                                    <span className="font-bold text-lg">{pair}</span>
                                    <span className={`px-2 py-0.5 rounded text-xs font-bold ${decision === 'BUY' ? 'bg-green-500/20 text-green-500' : decision === 'SELL' ? 'bg-red-500/20 text-red-500' : 'bg-yellow-500/20 text-yellow-500'}`}>
                                        {decision || 'HOLD'} ({confidence?.toFixed(1)}%)
                                    </span>
                                </div>

                                <div className="h-4 bg-muted rounded-full overflow-hidden flex relative">
                                    <div style={{ width: `${buyPct}%` }} className="bg-green-500 transition-all duration-500" />
                                    <div style={{ width: `${sellPct}%` }} className="bg-red-500 transition-all duration-500" />

                                    {/* Threshold Marker (75%) */}
                                    <div className="absolute top-0 bottom-0 w-0.5 bg-white/50 left-[75%]" title="Buy Threshold" />
                                    <div className="absolute top-0 bottom-0 w-0.5 bg-white/50 left-[25%]" title="Sell Threshold" />
                                </div>

                                <div className="flex justify-between text-xs text-muted-foreground">
                                    <span>BUY Power: {buy.toFixed(1)}</span>
                                    <span>SELL Power: {sell.toFixed(1)}</span>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
};

export default BrainVoting;
