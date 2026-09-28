"""Publish the latest 0.1.68 fixes as 0.9.0, with original/0.1.65 routes.

Master 0.1.68 with relayout_disc.py, then name the verified release image
ACE3-English-0.9.0-orig-layout.iso. Refresh the local upstream tools checkout
and inspect its release standard before running this dry-run-first packager.
"""
import package_release_047 as package

package.VERSION = '0.9.0'
package.MOVIE = package.DIR/'ACE3-English-0.9.0-orig-layout.iso'
package.OUTPUT = package.ROOT/'work/output/release-0.9.0'
package.TOOLS = package.ROOT/'work/local/retro-trans-release-065'
PREVIOUS = package.DIR/'ACE3-English-0.1.64-orig-layout.iso'
package.EXPECTED = {
    package.ORIGINAL: '5264079d36d953f464b166052e1ddea9be22a84c30a9333da24b8e1471311705',
    PREVIOUS: 'b8d7f75e714eb2a0575bf9b7d79030bdc7859a75552b4560bb13e166f633486a',
}


def jobs():
    for version,source,name in [
        ('original',package.ORIGINAL,'ACE3-English-0.9.0-movie.xdelta'),
        ('0.1.65',PREVIOUS,'ACE3-English-0.1.65-to-0.9.0-movie.xdelta'),
    ]:
        yield dict(patch=name,edition='English prologue',language='en',
                   source_version=version,source_format='iso',target_format='iso',
                   source=str(source),target=str(package.MOVIE))


if __name__=='__main__':
    package.jobs=jobs
    package.main()
