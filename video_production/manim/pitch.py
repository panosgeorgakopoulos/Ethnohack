"""Transition and closing scenes for the unified submission pitch."""
from common import *
import common
common.SCALE = 1.3

class PitchScene(NarratedMixin, Scene):
    VIDEO = 'pitch'
    def setup(self):
        self.camera.background_color = GROUND
    def heading(self, small, title):
        a = txt(small.upper(), 17, ACCENT, MEDIUM)
        b = txt(title, 48, INK, MEDIUM)
        return VGroup(a,b).arrange(DOWN, aligned_edge=LEFT, buff=.25).to_corner(UL,buff=.65)

class PTransition(PitchScene):
    SID = 'p_transition'
    def construct(self):
        self.start_narration()
        self.play(FadeIn(self.heading('Guided demonstration', 'Three assays. One decision.')),run_time=.7)
        steps = [('01','Choose the pair'),('02','Inspect the contrast'),('03','Reveal each assay'),('04','Review and export')]
        g=VGroup()
        for i,(n,t) in enumerate(steps):
            row=VGroup(txt(n,32,ACCENT,MEDIUM),txt(t,30,INK)).arrange(RIGHT,buff=.5)
            g.add(row)
        g.arrange(DOWN,aligned_edge=LEFT,buff=.42).move_to(LEFT*2+DOWN*.35)
        self.play(LaggedStart(*[FadeIn(r,shift=RIGHT*.15) for r in g],lag_ratio=.3),run_time=2)
        note=txt('Reconstruction of captured engine states · archived ENPKG measurements',17,MUTED).to_edge(DOWN,buff=.8)
        self.play(FadeIn(note),run_time=.4)
        self.finish()

class PClose(PitchScene):
    SID = 'p_close'
    def construct(self):
        self.start_narration()
        h=self.heading('Technology', 'An inspectable decision trail')
        stack=VGroup(txt('Python  /  NumPy  /  RDKit',33,INK,MEDIUM),txt('Browser workbench  /  JSON export',27,MUTED)).arrange(DOWN,aligned_edge=LEFT,buff=.35).move_to(LEFT*.4)
        self.play(FadeIn(h),FadeIn(stack),run_time=.6)
        self.at('impact')
        self.play(FadeOut(h),FadeOut(stack),run_time=.4)
        h=self.heading('Potential impact', 'Fewer premature isolation decisions')
        items=VGroup(txt('01   Blinded comparison with strongest-first',27,INK),txt('02   Broader hard cases and model stress tests',27,INK),txt('03   Purified-compound and mixture experiments',27,INK)).arrange(DOWN,aligned_edge=LEFT,buff=.5).move_to(DOWN*.15)
        self.play(FadeIn(h),LaggedStart(*[FadeIn(r) for r in items],lag_ratio=.2),run_time=1.2)
        self.at('limits')
        limit=txt('Research hypotheses. Nothing is clinically validated.',23,ACCENT,MEDIUM).to_edge(DOWN,buff=.9)
        self.play(FadeIn(limit),run_time=.4)
        self.at('team')
        self.play(FadeOut(h),FadeOut(items),FadeOut(limit),run_time=.5)
        end=VGroup(txt('DECOUPLE',57,INK,MEDIUM),txt('Which assay breaks the tie?',29,ACCENT),txt('Panos Georgakopoulos  ·  Apostolos Dedeloudis',23,MUTED)).arrange(DOWN,buff=.45)
        self.play(FadeIn(end),run_time=.6)
        self.finish(fade=False)
