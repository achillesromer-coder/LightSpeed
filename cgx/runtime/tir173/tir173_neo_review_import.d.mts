/** Untrusted, owner-selected local Neo review presentation; no runtime authority. */
export type NeoLocalReviewCase = {
 index:number;
 input:string;
 status:'EXACT_CANONICAL_REVIEW_PLAN'|'ABSTAIN_REVIEW_REQUIRED';
 human_summary:string;
 guard_reason:string|null;
 model_candidate:string|null;
 intuitive:string;
 deliberative:string;
 assurance:string;
 privileged_action:false;
};
export type NeoLocalReview = {
 schema:'cgx.neo.guios_local_preview/0.1';
 owner_selected_file_only:true;
 imported_packet_unverified:true;
 checkpoint_sha256_claim:string;
 total_cases:number;
 exact_review_plans:number;
 guarded_abstentions:number;
 native_effects:0;
 model_weights_verified_by_browser:false;
 items:NeoLocalReviewCase[];
};
export declare function reviewLocalNeoBatch(value:unknown):NeoLocalReview;
