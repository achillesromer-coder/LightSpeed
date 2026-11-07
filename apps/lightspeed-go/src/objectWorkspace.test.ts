import {it,expect} from 'vitest';
import {resolveObjectWindows} from './osShellModel';
it('resolves one active existing pane without duplicate windows or arbitrary routes',()=>{
 expect(resolveObjectWindows(['press','press','load','https://external'],'load')).toEqual({open:['press','load'],active:'load'});
 expect(resolveObjectWindows([],null)).toEqual({open:['press'],active:'press'});
 expect(resolveObjectWindows(['family'],'closed')).toEqual({open:['family'],active:'family'});
});
