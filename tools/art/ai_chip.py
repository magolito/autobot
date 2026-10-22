"""Isometric "AI chip" illustration for the Plans page (pure SVG, generated). Imported by build_plans.py."""
import math
COS,SIN=math.cos(math.radians(30)),math.sin(math.radians(30))
U=24
def P(x,y,z): return ((x-y)*COS*U, (x+y)*SIN*U - z*U)
def pts(*ps): return ' '.join(f'{a:.1f},{b:.1f}' for a,b in ps)
def box(x,y,w,d,h,z=0,cls=''):
    t=[P(x,y,z+h),P(x+w,y,z+h),P(x+w,y+d,z+h),P(x,y+d,z+h)]
    l=[P(x,y+d,z+h),P(x+w,y+d,z+h),P(x+w,y+d,z),P(x,y+d,z)]
    r=[P(x+w,y,z+h),P(x+w,y+d,z+h),P(x+w,y+d,z),P(x+w,y,z)]
    return f'<g class="iso {cls}"><polygon class="f-l" points="{pts(*l)}"/><polygon class="f-r" points="{pts(*r)}"/><polygon class="f-t" points="{pts(*t)}"/></g>'
N=14; Z=.35; C=7
parts=[box(0,0,N,N,Z,cls='plate')]
chips=[('Price',(6,0.8)),('Sentiment',(11.2,6)),('On-chain',(6,11.2)),('News',(0.8,6))]
for i,(n,(cx,cy)) in enumerate(chips):
    sx,sy=cx+1,cy+1
    for off in (-.55,0,.55):
        if i in (0,2):
            a=(sx+off,sy+(1 if i==0 else -1)); b=(sx+off,5 if i==0 else 9)
        else:
            a=(sx+(-1 if i==1 else 1),sy+off); b=(9 if i==1 else 5,sy+off)
        p1,p2=P(*a,Z),P(*b,Z); d=f'M{p1[0]:.1f} {p1[1]:.1f} L{p2[0]:.1f} {p2[1]:.1f}'
        if off==0: parts.append(f'<path class="tr-base" d="{d}"/><path class="tr-flow" style="--d:{i*.45:.2f}s" d="{d}"/>')
        else: parts.append(f'<path class="tr-base thin" d="{d}"/>')
objs=[(cx+cy, box(cx,cy,2,2,.7,Z,cls='chip')) for n,(cx,cy) in chips]+[(14, box(5,5,4,4,1.5,Z,cls='core'))]
for _,g in sorted(objs,key=lambda o:o[0]): parts.append(g)
ct=Z+1.5
parts.append(f'<polygon class="core-die" points="{pts(P(5.9,5.9,ct),P(8.1,5.9,ct),P(8.1,8.1,ct),P(5.9,8.1,ct))}"/>')
for gx in range(3):
    for gy in range(3):
        x,y=6.15+gx*.62,6.15+gy*.62
        parts.append(f'<polygon class="cell" style="--i:{(gx*3+gy)%5}" points="{pts(P(x,y,ct),P(x+.42,y,ct),P(x+.42,y+.42,ct),P(x,y+.42,ct))}"/>')
cx0,cy0=P(C,C,Z)
for i,(n,(cx,cy)) in enumerate(chips):
    parts.append(f'<polygon class="pin" style="--d:{i*.45:.2f}s" points="{pts(P(cx+.6,cy+.6,Z+.7),P(cx+1.4,cy+.6,Z+.7),P(cx+1.4,cy+1.4,Z+.7),P(cx+.6,cy+1.4,Z+.7))}"/>')
    x,y=P(cx+1,cy+1,Z+.7); dx,dy=x-cx0,y-cy0; L=math.hypot(dx,dy); x+=dx/L*(78 if dy<0 else 70); y+=dy/L*(40 if dy<0 else 96)
    anchor='start' if dx>0 else 'end'
    parts.append(f'<text class="lb" x="{x:.1f}" y="{y+4:.1f}" text-anchor="{anchor}">{n}</text>')
# viewBox from plate corners
cs=[P(0,0,Z),P(N,0,Z),P(N,N,0),P(0,N,0)]
minx=min(c[0] for c in cs)-70; maxx=max(c[0] for c in cs)+70; miny=min(c[1] for c in cs)-30; maxy=max(c[1] for c in cs)+30
SVG=f'<svg class="chipart" viewBox="{minx:.0f} {miny:.0f} {maxx-minx:.0f} {maxy-miny:.0f}" role="img" aria-label="Price, sentiment, news and on-chain signals flow into the built-in AI in AutoBot Pro.">'+''.join(parts)+'</svg>'
