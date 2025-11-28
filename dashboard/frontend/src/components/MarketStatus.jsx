import React from 'react';
import { Globe } from 'lucide-react';

const MarketStatus = ({ data }) => {
    const { sessions = [], liquidity = 'UNKNOWN' } = data;

    return (
        <div className="bg-card border border-border rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
                <Globe className="w-5 h-5 text-primary" />
                <h2 className="text-lg font-semibold">Market Status</h2>
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div className="bg-muted/50 p-3 rounded-lg">
                    <div className="text-xs text-muted-foreground mb-1">Active Sessions</div>
                    <div className="font-medium flex flex-wrap gap-1">
                        {sessions.length > 0 ? sessions.map(s => (
                            <span key={s} className="bg-background px-1.5 py-0.5 rounded text-xs border border-border">{s}</span>
                        )) : <span className="text-muted-foreground">-</span>}
                    </div>
                </div>

                <div className="bg-muted/50 p-3 rounded-lg">
                    <div className="text-xs text-muted-foreground mb-1">Liquidity</div>
                    <div className={`font-bold ${liquidity === 'HIGH' ? 'text-green-500' : liquidity === 'LOW' ? 'text-red-500' : 'text-yellow-500'}`}>
                        {liquidity}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default MarketStatus;
