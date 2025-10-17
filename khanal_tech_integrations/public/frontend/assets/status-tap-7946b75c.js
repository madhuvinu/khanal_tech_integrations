import{r as i,a,b as m}from"./Sample-73619dde.js";import{f as c,s as d}from"./index8-db7a4240.js";import"./index-d15d2ffa.js";import"./Dropdown-da2e9b4a.js";/*!
 * (C) Ionic http://ionicframework.com - MIT License
 */const h=()=>{const e=window;e.addEventListener("statusTap",()=>{i(()=>{const n=e.innerWidth,s=e.innerHeight,o=document.elementFromPoint(n/2,s/2);if(!o)return;const t=c(o);t&&new Promise(r=>a(t,r)).then(()=>{m(async()=>{t.style.setProperty("--overflow","hidden"),await d(t,300),t.style.removeProperty("--overflow")})})})})};export{h as startStatusTap};
//# sourceMappingURL=status-tap-7946b75c.js.map
