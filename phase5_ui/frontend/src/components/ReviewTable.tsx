'use client';

import { Star } from 'lucide-react';

interface Review {
  reviewId: string;
  content: string;
  score: number;
  at: string;
}

interface ReviewTableProps {
  reviews: Review[];
}

export default function ReviewTable({ reviews }: ReviewTableProps) {
  return (
    <div className="glass-card rounded-2xl overflow-hidden shadow-2xl">
      <div className="px-6 py-5 border-b border-slate-700/50 flex justify-between items-center">
        <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest">Feedback Stream</h3>
        <div className="flex gap-2">
          <span className="px-2 py-1 bg-blue-500/10 text-blue-400 text-[10px] font-bold rounded uppercase">{reviews.length} entries</span>
        </div>
      </div>
      <div className="overflow-x-auto max-h-[600px]">
        <table className="w-full text-left">
          <thead className="bg-slate-800/50 sticky top-0 backdrop-blur-md">
            <tr>
              <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Sentiment</th>
              <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest">Content</th>
              <th className="px-6 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-widest text-right">Date</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {reviews.map((review) => (
              <tr key={review.reviewId} className="group hover:bg-slate-700/30 transition-all duration-300">
                <td className="px-6 py-5 align-top">
                  <div className="flex items-center gap-1.5 px-3 py-1 bg-slate-800 rounded-lg w-fit group-hover:bg-slate-700">
                    <Star size={12} className={review.score >= 4 ? "fill-blue-400 text-blue-400" : "fill-slate-500 text-slate-500"} />
                    <span className={`text-sm font-bold ${review.score >= 4 ? "text-blue-400" : "text-slate-400"}`}>
                      {review.score}.0
                    </span>
                  </div>
                </td>
                <td className="px-6 py-5 text-sm text-slate-300 leading-relaxed max-w-2xl">
                  {review.content}
                </td>
                <td className="px-6 py-5 text-[11px] text-slate-500 font-medium whitespace-nowrap text-right align-top">
                  {new Date(review.at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
