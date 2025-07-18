from slurm_dashboard.walltime import WallTime


def test_walltime_parse():
    wt = WallTime.from_string('1-02:03:04')
    assert wt.days == 1
    assert wt.hours == 2
    assert wt.minutes == 3
    assert wt.seconds == 4
    assert str(wt) == '1-02:03:04'
    assert wt.to_seconds() == 1*86400 + 2*3600 + 3*60 + 4
