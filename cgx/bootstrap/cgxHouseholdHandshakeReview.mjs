/**
 * Generic preflight for caller-supplied device ROLE candidates, never a scan.
 * Native OS ownership, keystore, consent, proximity and signed lease remain
 * independent prerequisites even if all client-provided claims say "true".
 */
export const SCHEMA='CGX-DEVICE-ROLE-PREFLIGHT/0.1';
const kinds=new Set(['computer','phone','watch','console','television','laptop','other']);
const relations=new Set(['owner_claim','other_user','excluded']);
const ranges=new Set(['local','unknown','out_of_range']);
const keyOK=v=>typeof v==='string'&&/^[a-z0-9][a-z0-9_-]{0,62}$/.test(v);
const deny=reason=>({schema:SCHEMA,state:'DENIED',reason,scan:false,pair:false,mint:false});
export function planDeviceRolePreflight({candidates=[]}={}){
 if(!Array.isArray(candidates)||candidates.length>24)return deny('INVALID_DEVICE_ROLE_LIST');
 const keys=new Set(),devices=[];
 for(const c of candidates){
  if(!c||typeof c!=='object'||Array.isArray(c)||
     Object.keys(c).some(k=>!['key','kind','relationship','proximity'].includes(k))||
     !keyOK(c.key)||!kinds.has(c.kind)||!relations.has(c.relationship)||
     !ranges.has(c.proximity)||keys.has(c.key))return deny('INVALID_OR_DUPLICATE_DEVICE_ROLE');
  keys.add(c.key);
  const status=c.relationship==='excluded'?'DENY_NOT_OWNED':
   c.relationship==='other_user'&&c.proximity==='out_of_range'?
   'DENY_OTHER_USER_OUT_OF_RANGE':c.relationship==='other_user'?
   'DENY_OTHER_USER_CONSENT_REQUIRED':'HOLD_INDEPENDENT_NATIVE_ACCEPTANCE';
  devices.push({
   ...c,status,
   physical_identity_verified:false,owner_os_consent_verified:false,
   authenticated_lease_verified:false,
   may_scan:false,may_pair:false,may_hydrate:false,may_mint:false
  });
 }
 return {schema:SCHEMA,state:'SOURCE_REVIEW_ONLY',devices,
  role_count:devices.length,
  denied_count:devices.filter(x=>x.status.startsWith('DENY')).length,
  pending_count:devices.filter(x=>x.status.startsWith('HOLD')).length,
  native_admitted:false,network_scan_performed:false,
  bluetooth_scan_performed:false,physical_pairing_performed:false,
  network_transfer:false,canonical_mutation:false,
  note:'Client role claims can never authorise a native handshake, a peer or an Object_ID.'};
}
